from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import CompletionStatus


class GPSPointCreate(BaseModel):
    sequence: int = Field(ge=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_meters: Optional[float] = Field(default=None, ge=0)
    recorded_at: datetime


class TreatmentSessionCreate(BaseModel):
    technician_id: int
    started_at: datetime
    stopped_at: datetime
    completion_status: CompletionStatus = CompletionStatus.COMPLETED
    gps_points: list[GPSPointCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_time_window(self) -> "TreatmentSessionCreate":
        if self.stopped_at < self.started_at:
            raise ValueError("stopped_at must be greater than or equal to started_at")
        return self


class GPSPointRead(BaseModel):
    id: int
    sequence: int
    latitude: float
    longitude: float
    accuracy_meters: Optional[float]
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TreatmentSessionRead(BaseModel):
    id: int
    job_id: int
    technician_id: int
    started_at: datetime
    stopped_at: datetime
    duration_seconds: int
    distance_meters: float
    completion_status: CompletionStatus
    gps_points: list[GPSPointRead]

    model_config = ConfigDict(from_attributes=True)
