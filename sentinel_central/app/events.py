from typing import List, Optional, Annotated, Literal, Union, Dict
from pydantic import BaseModel, Field, AliasChoices, TypeAdapter, field_validator, model_validator, validator
import re

class BBox(BaseModel):
    l: float
    t: float
    r: float
    b: float

ATTR_ORDER = [
    'Age-Young', 'Age-Adult', 'Age-Old', 'Gender-Female', 'Hair-Length-Short', 'Hair-Length-Long', 'Hair-Length-Bald', 'UpperBody-Length-Short', 
    'UpperBody-Color-Black', 'UpperBody-Color-Blue', 'UpperBody-Color-Brown', 'UpperBody-Color-Green', 'UpperBody-Color-Grey', 
    'UpperBody-Color-Orange', 'UpperBody-Color-Pink', 'UpperBody-Color-Purple', 'UpperBody-Color-Red', 'UpperBody-Color-White', 
    'UpperBody-Color-Yellow', 'UpperBody-Color-Other', 'LowerBody-Length-Short', 'LowerBody-Color-Black', 'LowerBody-Color-Blue', 
    'LowerBody-Color-Brown', 'LowerBody-Color-Green', 'LowerBody-Color-Grey', 'LowerBody-Color-Orange', 'LowerBody-Color-Pink', 
    'LowerBody-Color-Purple', 'LowerBody-Color-Red', 'LowerBody-Color-White', 'LowerBody-Color-Yellow', 'LowerBody-Color-Other', 
    'LowerBody-Type-Trousers&Shorts', 'LowerBody-Type-Skirt&Dress', 'Accessory-Backpack', 'Accessory-Bag', 'Accessory-Glasses-Normal', 
    'Accessory-Glasses-Sun', 'Accessory-Hat']

assert len(ATTR_ORDER) == 40
ATTR_INDEX = {n: i for i, n in enumerate(ATTR_ORDER)}
_ATTR_RE = re.compile(r"^(?P<name>.+?)\s*\((?P<score>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\)\s*$")


# Edge → Central
class ParEventPayload(BaseModel):
    # core routing
    event_type: Literal['appearance', 'disappearance']
    track_id: str

    # topology
    location_id: str
    camera_id: str
    edge_id: str

    # content
    frame: int
    bbox_ltrb: List[int] = Field(min_items=4, max_items=4)
    image_path: Optional[str] = None
    
     # attributes: either strings OR a fixed 40-dim vector
    attributes: Optional[List[str]] = None
    attributes_vec: Optional[List[float]] = Field(default=None, min_items=40, max_items=40)

    # embedding: 512 floats for appearance; can be empty or omitted for disappearance
    embedding: Optional[List[float]] = Field(default=None, min_items=0, max_items=512)


    @field_validator("bbox_ltrb")
    def _bbox_ints(cls, v):
        if any(not isinstance(x, int) for x in v):
            raise ValueError("bbox_ltrb must be [l,t,r,b] with integers")
        return v
    
    @field_validator("attributes_vec")
    def _attr_vec_len(cls, v):
        if v is None:
            return None
        if len(v) != 40:
            raise ValueError("attributes_vec must be length 40")
        return v
    
    def parse_attributes(self):
        """
        Returns (attributes_json, attr_scores_vec_or_none).
        attributes_json = {'items': [{'name': str, 'score': float}, ...]}
        attr_scores_vec_or_none = list[40] or None
        """
        items = []
        vec = None

        if self.attributes_vec is not None:
            # authoritative vector present
            vec = list(map(float, self.attributes_vec))
            # also build items for readability using canonical names
            items = [{"name": ATTR_ORDER[i], "score": float(vec[i])} for i in range(40)]
        elif self.attributes:
            # parse strings like "Age Adult (0.96)"
            tmp = [0.0] * 40
            for s in self.attributes:
                m = _ATTR_RE.match(s.strip())
                if not m:
                    continue
                name = m.group("name")
                score = float(m.group("score"))
                items.append({"name": name, "score": score})
                if name in ATTR_INDEX:
                    tmp[ATTR_INDEX[name]] = score
            vec = tmp

        return {"items": items}, (vec if items or self.attributes_vec is not None else None)


# Central: IDF enrichment
class TtsEventPayload(ParEventPayload):
    idf_name: str
    resolved_id: Optional[str]
    resolved_at_ms: int
    best_distance: float
    second_distance: Optional[float]
    is_new_identity: bool

# Abnormal activity
class AdEventPayload(BaseModel):
    phase: Literal["start", "end"]

    # accept either "episode" or "episode_id" in the incoming JSON
    episode: str = Field(..., validation_alias=AliasChoices("episode", "episode_id"))

    incident: str = "anomaly"
    confidence: float = 0.0
    location_id: str
    camera_id: str
    edge_id: str

    image_path: Optional[str] = None
    image_b64: Optional[str] = None
    ext: Optional[str] = None

    # timestamps (optional by default)
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    duration_ms: Optional[int] = None  # usually computed in DB or by server

    @field_validator("phase", mode="before")
    @classmethod
    def _norm_phase(cls, v):  # handle "START", "End", etc.
        return str(v).lower()
    
    @model_validator(mode="after")
    def _phase_requirements(self):
        if self.phase == "start" and self.start_ms is None:
            raise ValueError("start_ms is required when phase='start'")
        if self.phase == "end" and self.end_ms is None:
            raise ValueError("end_ms is required when phase='end'")
        return self


# Movement/geofence change
class MovementUpdatePayload(BaseModel):
    movement_type: Literal['Move-In', 'Move-Out']
    resolved_id: str
    annotation_name: Optional[str] = None
    location_id: str
    camera_id: str
    edge_id: str
    ts_ms: int
    track_id: Optional[str] = None
