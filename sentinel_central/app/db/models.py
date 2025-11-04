from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from sqlalchemy import (
    BigInteger, String, Boolean, JSON, Text, Integer,
    Index, UniqueConstraint, ARRAY, Enum as SQLEnum
)
from pgvector.sqlalchemy import Vector

from enum import Enum
from typing import List, Optional

Base = declarative_base()

class ParEventORM(Base):
    __tablename__ = "par_events"

    # existing
    id: Mapped[int]                = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    track_id: Mapped[str]          = mapped_column(String(128), index=True)
    resolved_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    appeared: Mapped[bool]         = mapped_column(Boolean)
    meta: Mapped[Optional[dict]]   = mapped_column(JSON, nullable=True)
    ts_ms: Mapped[int]             = mapped_column(BigInteger, index=True)

    # NEW topology
    cam_id: Mapped[Optional[str]]        = mapped_column(Text, index=True)
    edge_id: Mapped[Optional[str]]       = mapped_column(Text, index=True)
    location_id: Mapped[Optional[str]]   = mapped_column(Text, index=True)

    # NEW geometry + vectors
    bbox_ltrb: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer, dimensions=1), nullable=True)
    embedding: Mapped[Optional[list]]      = mapped_column(Vector(512), nullable=True)   # pgvector (nullable)
    attributes: Mapped[Optional[dict]]     = mapped_column(JSON, nullable=True)          # explainable
    attr_scores: Mapped[Optional[list]]    = mapped_column(Vector(40), nullable=True)    # 40-dim vector

    __table_args__ = (
        Index("ix_par_resolved_ts", "resolved_id", "ts_ms"),
        Index("ix_par_cam_ts", "cam_id", "ts_ms"),
        Index("ix_par_edge_ts", "edge_id", "ts_ms"),
        Index("ix_par_loc_ts", "location_id", "ts_ms"),
        UniqueConstraint("cam_id", "track_id", "ts_ms", name="uq_par_cam_track_ts"),
    )


class ADPhase(str, Enum):
    START = "start"
    END   = "end"

class AdEventORM(Base):
    __tablename__ = "ad_events"
    __table_args__ = {"schema": "public"}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    phase: Mapped[ADPhase] = mapped_column(
        SQLEnum(
            ADPhase,
            name="ad_phase_start_end",
            create_type=False,                    # type already exists in PG
            values_callable=lambda e: [m.value for m in e],  # <- store 'start'/'end'
            validate_strings=True,                # allow assigning "start"/"end" too
        ),
        nullable=False,
        server_default="start",
    )
    episode: Mapped[str] = mapped_column(String(64), index=True)  # UUID/handle for the episode
    incident: Mapped[str] = mapped_column(String(128), index=True)
    confidence: Mapped[float]
    location_id: Mapped[str] = mapped_column(String(128), index=True)
    camera_id: Mapped[str] = mapped_column(String(128), index=True)
    edge_id: Mapped[str] = mapped_column(String(128), index=True)

    image_path: Mapped[str | None]   = mapped_column(Text)

    # event timing
    start_ms: Mapped[int] = mapped_column(BigInteger, index=True, nullable=True)
    end_ms:   Mapped[Optional[int]] = mapped_column(BigInteger, index=True, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(BigInteger, index=True, nullable=True)

class MovementORM(Base):
    __tablename__ = "movements"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    resolved_id: Mapped[str] = mapped_column(String(128), index=True)
    track_id: Mapped[str] = mapped_column(String(256), index=True, nullable=True)
    annotation_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    state: Mapped[str] = mapped_column(String(64))
    location_id: Mapped[str] = mapped_column(String(128), index=True)
    camera_id: Mapped[str] = mapped_column(String(128), index=True)
    edge_id: Mapped[str] = mapped_column(String(128), index=True)
    ts_ms: Mapped[int] = mapped_column(BigInteger, index=True)

    __table_args__ = (Index("ix_mv_resolved_ts", "resolved_id", "ts_ms"),)



class PersonSessionORM(Base):
    __tablename__ = "person_sessions"

    session_id: Mapped[int]      = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id: Mapped[str]              = mapped_column(Text, nullable=False)            # display/session ID
    resolved_id: Mapped[str]     = mapped_column(Text, nullable=False)            # identities.id
    track_id: Mapped[Optional[str]] = mapped_column(String(256), index=True, nullable=True)
    location_id: Mapped[str | None] = mapped_column(Text, index=True)
    camera_id: Mapped[str | None]   = mapped_column(Text, index=True)
    appear_ms: Mapped[int]       = mapped_column(BigInteger, index=True)
    disappear_ms: Mapped[int | None] = mapped_column(BigInteger, index=True)
    attributes: Mapped[dict | None]  = mapped_column(JSON)
    attr_scores: Mapped[list | None] = mapped_column(Vector(40), nullable=True)
    attr_names: Mapped[list | None]  = mapped_column(JSON)        # list[str]
    embedding: Mapped[list | None]   = mapped_column(Vector(512), nullable=True)
    image_path: Mapped[str | None]   = mapped_column(Text)