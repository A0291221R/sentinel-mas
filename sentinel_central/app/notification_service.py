import base64
import os
import pathlib
from typing import Dict, Any, Optional
from app.events import AdEventPayload, MovementUpdatePayload
from app.db.db import get_session
from app.db.models import ADPhase, AdEventORM, MovementORM
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

import logging
log = logging.getLogger(__name__)



MEDIA_ROOT = os.getenv("MEDIA_ROOT", "D:/app/sentinel-central/")  # Streamlit can read this folder

def _event_file_path(episode: str, camera_id: str, start_ms: int, ext: str = "jpg") -> str:
    folder = pathlib.Path(MEDIA_ROOT) / "snapshots/anomaly_events" / episode
    folder.mkdir(parents=True, exist_ok=True)
    return str(folder / f"start-{camera_id}-{int(start_ms)}.{ext}")


class RealtimeAlertNotification:
    def __init__(self, created_by: str = "ran-svc-1"):
        self.created_by = created_by

    async def handle_ad_event(self, envelope: Dict[str, Any]) -> None:
        log.info(f'handle AD-event with "start"...{envelope}')
        p = AdEventPayload(**envelope["payload"])
        episode: Optional[str] = getattr(p, "episode", None) or getattr(p, "episode_id", None)
        if not episode:
            log.error("AD payload missing episode/episode_id: %s", envelope)
            return

        phase = ADPhase(str(p.phase).lower())
        # optional: validate timestamps in payload
        if phase == ADPhase.START and p.start_ms is None:
            log.warning("START received without start_ms for episode=%s", episode)
        if phase == ADPhase.END and p.end_ms is None:
            log.warning("END received without end_ms for episode=%s", episode)
        try:
            async with get_session() as s:  # type: AsyncSession
                res = await s.execute(select(AdEventORM).where(AdEventORM.episode == episode))
                row: Optional[AdEventORM] = res.scalar_one_or_none()

                if phase == ADPhase.START:
                    img_b64 = p.image_b64
                    img_path = None
                    if img_b64:
                        try:
                            ext = (p.ext or "jpg").lstrip(".")
                            img_path = _event_file_path(episode, p.camera_id, p.start_ms, ext)
                            raw = base64.b64decode(img_b64, validate=True)
                            with open(img_path, "wb") as f:
                                f.write(raw)
                            img_path = str(pathlib.Path(img_path).resolve())
                            log.debug("Saved AD snapshot to %s", img_path)
                        except Exception as e:
                            log.warning("Failed to decode/write AD image for episode=%s: %s", episode, e)
                            img_path = None
                    else:
                        print(f'img_b64 is None...')

                    if row is None:
                        log.info(f'handle AD-event START, addnew"...{row}')
                        row = AdEventORM(
                            phase=ADPhase.START,
                            episode=episode,
                            incident=p.incident,
                            confidence=float(p.confidence or 0.0),
                            location_id=p.location_id,
                            camera_id=p.camera_id,
                            edge_id=p.edge_id,
                            start_ms=p.start_ms,
                            image_path=img_path,
                            # end_ms=None, duration_ms=None  (let DB compute if generated)
                        )
                        s.add(row)
                    else:
                        log.info(f'handle AD-event START, update"...{row}')
                        row.phase = ADPhase.START
                        if p.start_ms is not None:
                            row.start_ms = min(row.start_ms, p.start_ms) if row.start_ms else p.start_ms
                        # refresh identifiers & keep max confidence
                        row.incident = p.incident or row.incident
                        row.location_id = p.location_id or row.location_id
                        row.camera_id = p.camera_id or row.camera_id
                        row.edge_id = p.edge_id or row.edge_id
                        if p.confidence is not None:
                            row.confidence = max(float(row.confidence or 0.0), float(p.confidence or 0.0))

                elif phase == ADPhase.END:
                    if row is None:
                        log.debug(f'handle AD-event END, addNew...{row}')
                        # end-only event (start unknown) — still record it
                        row = AdEventORM(
                            phase=ADPhase.END,
                            episode=episode,
                            incident=p.incident,
                            confidence=float(p.confidence or 0.0),
                            location_id=p.location_id,
                            camera_id=p.camera_id,
                            edge_id=p.edge_id,
                            start_ms=p.start_ms,
                            end_ms=p.end_ms,
                            duration_ms=p.duration_ms
                        )
                        s.add(row)
                    else:
                        log.debug(f'handle AD-event END, update...{row}')
                        row.phase = ADPhase.END
                        if p.end_ms is not None:
                            row.end_ms = max(row.end_ms, p.end_ms) if row.end_ms else p.end_ms
                        row.incident = p.incident or row.incident
                        row.location_id = p.location_id or row.location_id
                        row.camera_id = p.camera_id or row.camera_id
                        row.edge_id = p.edge_id or row.edge_id
                        if p.confidence is not None:
                            row.confidence = max(float(row.confidence or 0.0), float(p.confidence or 0.0))
                        row.duration_ms = p.duration_ms
                        # If NOT using a generated column for duration_ms, compute it here:
                        # if row.start_ms is not None and row.end_ms is not None:
                        #     row.duration_ms = max(0, row.end_ms - row.start_ms)

                else:
                    log.error("Unknown AD phase %r for episode=%s", p.phase, episode)
                    return
                await s.commit()

        except SQLAlchemyError as e:
            log.exception("Failed to persist AD event episode=%s: %s", episode, e)

    async def handle_movement_update(self, envelope: Dict[str, Any]):
        p = MovementUpdatePayload(**envelope["payload"])
        log.info(f"MovementUpdate: {p.resolved_id} {p.annotation_name} {p.movement_type} at {p.location_id}")
        async with get_session() as s:
            label = p.annotation_name or p.resolved_id
            s.add(MovementORM(
                resolved_id=p.resolved_id,
                state=p.movement_type,
                location_id=p.location_id,
                camera_id=p.camera_id,
                edge_id=p.edge_id,
                ts_ms=envelope["ts_ms"],
                track_id = p.track_id,
                annotation_name=label,
            ))
            await s.commit()
        
