from __future__ import annotations

from datetime import date, datetime
from typing import Optional, TypeVar

from sqlalchemy import JSON, Date, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import CompletionStatus, JobStatus, ServiceType

EnumType = TypeVar("EnumType")


def enum_column(enum_class: type[EnumType]) -> SAEnum:
    return SAEnum(
        enum_class,
        values_callable=lambda choices: [choice.value for choice in choices],
        native_enum=False,
        validate_strings=True,
    )


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    technicians: Mapped[list["Technician"]] = relationship(back_populates="tenant")
    customers: Mapped[list["Customer"]] = relationship(back_populates="tenant")
    properties: Mapped[list["Property"]] = relationship(back_populates="tenant")
    jobs: Mapped[list["Job"]] = relationship(back_populates="tenant")
    field_data_events: Mapped[list["FieldDataEvent"]] = relationship(back_populates="tenant")


class Technician(Base):
    __tablename__ = "technicians"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_technician_tenant_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="technicians")
    jobs: Mapped[list["Job"]] = relationship(back_populates="technician")
    treatment_sessions: Mapped[list["TreatmentSession"]] = relationship(back_populates="technician")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="customers")
    properties: Mapped[list["Property"]] = relationship(back_populates="customer")
    jobs: Mapped[list["Job"]] = relationship(back_populates="customer")


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    address_line1: Mapped[str] = mapped_column(String(180), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(80), default="Canada", nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="properties")
    customer: Mapped[Customer] = relationship(back_populates="properties")
    jobs: Mapped[list["Job"]] = relationship(back_populates="property")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "source_system", "external_job_id", name="uq_job_tenant_source_id"),
        UniqueConstraint(
            "tenant_id",
            "source_system",
            "external_road_id",
            "external_road_customer_id",
            name="uq_job_tenant_source_road_stop",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True, nullable=False)
    technician_id: Mapped[int] = mapped_column(ForeignKey("technicians.id"), index=True, nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    service_type: Mapped[ServiceType] = mapped_column(enum_column(ServiceType), nullable=False)
    status: Mapped[JobStatus] = mapped_column(enum_column(JobStatus), default=JobStatus.SCHEDULED, nullable=False)
    source_system: Mapped[str] = mapped_column(String(80), default="manual", nullable=False)
    external_job_id: Mapped[Optional[str]] = mapped_column(String(120), index=True, nullable=True)
    external_road_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    external_road_customer_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    external_road_customer_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    external_activity_ids: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    external_customer_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    external_technician_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    service_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    crm_treatment_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="jobs")
    customer: Mapped[Customer] = relationship(back_populates="jobs")
    property: Mapped[Property] = relationship(back_populates="jobs")
    technician: Mapped[Technician] = relationship(back_populates="jobs")
    treatment_sessions: Mapped[list["TreatmentSession"]] = relationship(back_populates="job")


class TreatmentSession(Base):
    __tablename__ = "treatment_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True, nullable=False)
    technician_id: Mapped[int] = mapped_column(ForeignKey("technicians.id"), index=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    stopped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_meters: Mapped[float] = mapped_column(Float, nullable=False)
    completion_status: Mapped[CompletionStatus] = mapped_column(enum_column(CompletionStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job: Mapped[Job] = relationship(back_populates="treatment_sessions")
    technician: Mapped[Technician] = relationship(back_populates="treatment_sessions")
    gps_points: Mapped[list["GpsPoint"]] = relationship(
        back_populates="treatment_session",
        cascade="all, delete-orphan",
        order_by="GpsPoint.sequence",
    )


class GpsPoint(Base):
    __tablename__ = "gps_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    treatment_session_id: Mapped[int] = mapped_column(ForeignKey("treatment_sessions.id"), index=True, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    treatment_session: Mapped[TreatmentSession] = relationship(back_populates="gps_points")


class FieldDataEvent(Base):
    __tablename__ = "field_data_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="field_data_events")
