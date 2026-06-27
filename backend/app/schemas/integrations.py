from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums import JobStatus


class CrmTreatmentStartedEvent(BaseModel):
    source_system: str = Field(min_length=2, max_length=80)
    external_job_id: Optional[str] = Field(default=None, min_length=1, max_length=120)
    road_id: Optional[int] = Field(default=None, gt=0)
    road_customer_id: Optional[int] = Field(default=None, gt=0)
    road_customer_order: Optional[int] = Field(default=None, gt=0)
    activity_ids: list[int] = Field(default_factory=list)
    customer_id: Optional[int] = Field(default=None, gt=0)
    technician_user_id: Optional[int] = Field(default=None, gt=0)
    started_at: datetime
    technician_email: Optional[str] = None

    @model_validator(mode="after")
    def require_crm_identifier(self) -> "CrmTreatmentStartedEvent":
        has_road_customer = self.road_id is not None and self.road_customer_id is not None
        has_road_order = self.road_id is not None and self.road_customer_order is not None
        if not (self.external_job_id or has_road_customer or has_road_order):
            raise ValueError("Provide external_job_id, road_id plus road_customer_id, or road_id plus road_customer_order.")
        return self


class CrmTreatmentStartedResponse(BaseModel):
    job_id: int
    status: JobStatus
    source_system: str
    external_job_id: Optional[str] = None
    road_id: Optional[int] = None
    road_customer_id: Optional[int] = None
    road_customer_order: Optional[int] = None
    activity_ids: list[int] = Field(default_factory=list)
    crm_treatment_started_at: datetime
