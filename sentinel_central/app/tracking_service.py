from typing import Dict, Any, Optional

import numpy as np
from app.common.repository import _get_tracking_info
from app.envelope import pack_event
from app.events import ParEventPayload, TtsEventPayload, MovementUpdatePayload
from app.bus import MessageBus
from app.db.db import get_session
from app.db.models import ParEventORM, MovementORM
from app.common.resolve import Resolver
from sqlalchemy import text
from app.services.sesessions import open_or_update_session_on_move_in, close_session_on_move_out


import logging

log = logging.getLogger(__name__)

class IDFusion:
    def __init__(self, bus: MessageBus, created_by: str = "idf-service-1"):
        self.bus = bus
        self.created_by = created_by
        self.resolver = Resolver(tau_same=0.22, tau_ambig=0.30, delta_min=0.05)

    async def handle_par_event(self, envelope: Dict[str, Any]):
        p = ParEventPayload(**envelope["payload"])

        appeared = p.event_type == "appearance"
        attrs_json, attrs_vec = p.parse_attributes()

        emb_list = None
        qvec = None

        if p.embedding:
            if len(p.embedding) != 512:
                log.warning("Bad embedding length=%d (expected 512); dropping", len(p.embedding))
            else:
                v = np.asarray(p.embedding, dtype=np.float32)
                n = float(np.linalg.norm(v))
                if not (0.999 <= n <= 1.001):
                    log.warning("Embedding not unit-norm (%.6f); edge should normalize", n)
                emb_list = v.tolist()
                qvec = v

        log.info(f"[IDFusion] par_event[{p.event_type}] from {envelope.get('created_by')} cam={p.camera_id} track={p.track_id}")

        resolved_id = None
        best = 1.0
        second = None
        is_new = False

        async with get_session() as s:
            # 1) persist the event first
            event = ParEventORM(
                track_id=p.track_id,
                resolved_id=None,            # fill below
                appeared=appeared,
                meta={
                    "event_type": p.event_type,
                    "image_path": getattr(p, "image_path", None),
                    "frame": getattr(p, "frame", None),
                    "edge_normed": True,
                },
                ts_ms=envelope["ts_ms"],
                cam_id=p.camera_id,
                edge_id=p.edge_id,
                location_id=p.location_id,
                bbox_ltrb=p.bbox_ltrb,
                embedding=emb_list,          # may be None for disappearance
                attributes=attrs_json or None,
                attr_scores=attrs_vec or None,
            )
            s.add(event)
            await s.flush()  # event.id available

            # 2) resolve identity only on appearance with a valid embedding
            if appeared and qvec is not None:
                resolved_id, best, second, is_new = await self.resolver.resolve(s, qvec, envelope["ts_ms"])
                event.resolved_id = resolved_id  # ✅ assign directly via ORM
                log.info(f'Resolved id {event.resolved_id} to track {event.track_id}')

            await s.commit()

        # 3) always publish TTS event
        # resolved_id could be None if it has only
        if not appeared or resolved_id:
            tts_payload = TtsEventPayload(
                **p.model_dump(),
                idf_name=self.created_by,
                resolved_id=event.resolved_id,
                resolved_at_ms=envelope["ts_ms"],
                best_distance=best,
                second_distance=second,
                is_new_identity=is_new,
            ).model_dump()

        await self.bus.publish_envelope(
            pack_event("tts-event", tts_payload, created_by=self.created_by)
        )

class TargetTrackingSystem:
    def __init__(self, bus: MessageBus, created_by: str = "tts-service-1"):
        self.bus = bus
        self.created_by = created_by

    async def handle_tts_event(self, envelope: Dict[str, Any]):
        p = TtsEventPayload(**envelope["payload"])
        movement_type = "Move-In" if p.event_type == "appearance" else "Move-Out"

        log.info(f'[TTS] receiving tts_event[{movement_type}] from {envelope.get("created_by")} rid={p.resolved_id}')

        async with get_session() as s:
            if movement_type == "Move-In":
                await open_or_update_session_on_move_in(
                    s,
                    resolved_id=p.resolved_id,
                    location_id=p.location_id,
                    camera_id=p.camera_id,
                    ts_ms=envelope["ts_ms"],
                    rep_image=p.image_path if hasattr(p, "image_path") else None,
                    rep_attrs=p.attributes if hasattr(p, "attributes") else None,
                    rep_attr_names=None,            # or derive from attributes
                    rep_scores=None,
                    rep_embedding=None,             # you can also forward qvec from IDF if carried in TTS
                    track_id=p.track_id if hasattr(p, "track_id") else None,
                )
            elif movement_type == "Move-Out":
                await close_session_on_move_out(
                    s, p.track_id, p.location_id, p.camera_id, envelope["ts_ms"]
                )

            # (A) Look up tracking flag + label while we still have the session
            is_tracked, annotation_name = await _get_tracking_info(s, p.resolved_id)
            await s.commit()

        if p.resolved_id and is_tracked:
            log.info(f'Tracked Person {annotation_name} {movement_type} from camera {p.camera_id} at location {p.location_id}')
            mu_payload = MovementUpdatePayload(
                movement_type=movement_type,
                resolved_id=p.resolved_id,
                annotation_name=annotation_name,   # ✅ now filled
                location_id=p.location_id,
                camera_id=p.camera_id,
                edge_id=p.edge_id,
                ts_ms=envelope["ts_ms"],
                track_id= p.track_id,
            ).model_dump()
            await self.bus.publish_envelope(pack_event("movement-update", mu_payload, created_by=self.created_by))
