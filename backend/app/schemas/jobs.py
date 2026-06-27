from __future__ import annotations

from datetime import date
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import JobStatus, ServiceType


class CustomerRead(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PropertyRead(BaseModel):
    id: int
    address_line1: str
    city: str
    region: str
    postal_code: str
    country: str

    model_config = ConfigDict(from_attributes=True)


class TechnicianRead(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class JobRead(BaseModel):
    id: int
    scheduled_date: date
    service_type: ServiceType
    service_name: Optional[str] = None
    status: JobStatus
    source_system: str
    external_job_id: Optional[str] = None
    external_road_id: Optional[int] = None
    external_road_customer_id: Optional[int] = None
    external_road_customer_order: Optional[int] = None
    external_activity_ids: list[int] = Field(default_factory=list)
    external_customer_id: Optional[int] = None
    external_technician_id: Optional[int] = None
    crm_treatment_started_at: Optional[datetime] = None
    customer: CustomerRead
    property: PropertyRead
    technician: TechnicianRead
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
