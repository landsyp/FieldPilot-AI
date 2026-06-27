from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_tenant
from app.db.database import get_db
from app.models import FieldDataEvent, GpsPoint, Job, JobStatus, Technician, Tenant, TreatmentSession
from app.schemas import CrmTreatmentStartedEvent, CrmTreatmentStartedResponse, JobRead, TreatmentSessionCreate, TreatmentSessionRead
from app.services.geo import total_distance_meters

router = APIRouter(prefix="/api", tags=["field-operations"])


def job_query():
    return select(Job).options(
        selectinload(Job.customer),
        selectinload(Job.property),
        selectinload(Job.technician),
    )


def add_field_data_event(
    db: Session,
    tenant_id: int,
    event_type: str,
    entity_type: str,
    entity_id: int,
    payload: dict,
) -> None:
    db.add(
        FieldDataEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )
    )


def crm_reference_payload(job: Job) -> dict:
    return {
        "source_system": job.source_system,
        "external_job_id": job.external_job_id,
        "road_id": job.external_road_id,
        "road_customer_id": job.external_road_customer_id,
        "road_customer_order": job.external_road_customer_order,
        "activity_ids": job.external_activity_ids,
        "customer_id": job.external_customer_id,
        "technician_user_id": job.external_technician_id,
    }


def find_job_for_crm_event(db: Session, tenant: Tenant, payload: CrmTreatmentStartedEvent) -> Optional[Job]:
    base_filters = [
        Job.tenant_id == tenant.id,
        Job.source_system == payload.source_system,
    ]

    if payload.road_id is not None and payload.road_customer_id is not None:
        job = db.scalar(
            select(Job).where(
                *base_filters,
                Job.external_road_id == payload.road_id,
                Job.external_road_customer_id == payload.road_customer_id,
            )
        )
        if job is not None:
            return job

    if payload.road_id is not None and payload.road_customer_order is not None:
        job = db.scalar(
            select(Job).where(
                *base_filters,
                Job.external_road_id == payload.road_id,
                Job.external_road_customer_order == payload.road_customer_order,
            )
        )
        if job is not None:
            return job

    if payload.external_job_id:
        return db.scalar(select(Job).where(*base_filters, Job.external_job_id == payload.external_job_id))

    return None


@router.get("/jobs/today", response_model=list[JobRead])
def list_today_jobs(
    service_date: Optional[date] = Query(default=None),
    technician_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
) -> list[Job]:
    target_date = service_date or date.today()
    statement = job_query().where(
        Job.tenant_id == tenant.id,
        Job.scheduled_date == target_date,
    )
    if technician_id is not None:
        statement = statement.where(Job.technician_id == technician_id)

    statement = statement.order_by(Job.id)
    return list(db.scalars(statement).all())


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
) -> Job:
    job = db.scalar(job_query().where(Job.id == job_id, Job.tenant_id == tenant.id))
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post(
    "/jobs/{job_id}/treatment-sessions",
    response_model=TreatmentSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_treatment_session(
    job_id: int,
    payload: TreatmentSessionCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
) -> TreatmentSession:
    job = db.scalar(select(Job).where(Job.id == job_id, Job.tenant_id == tenant.id))
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    technician = db.scalar(
        select(Technician).where(
            Technician.id == payload.technician_id,
            Technician.tenant_id == tenant.id,
        )
    )
    if technician is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Technician not found for tenant")
    if technician.id != job.technician_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Technician is not assigned to this job")
    if job.source_system == "vision_gazon_crm" and job.crm_treatment_started_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Start the treatment in Vision Gazon CRM before saving GPS tracking.",
        )

    duration_seconds = int((payload.stopped_at - payload.started_at).total_seconds())
    treatment_session = TreatmentSession(
        tenant_id=tenant.id,
        job_id=job.id,
        technician_id=technician.id,
        started_at=payload.started_at,
        stopped_at=payload.stopped_at,
        duration_seconds=max(duration_seconds, 0),
        distance_meters=total_distance_meters(payload.gps_points),
        completion_status=payload.completion_status,
    )
    db.add(treatment_session)
    db.flush()

    for point in payload.gps_points:
        db.add(
            GpsPoint(
                tenant_id=tenant.id,
                treatment_session_id=treatment_session.id,
                sequence=point.sequence,
                latitude=point.latitude,
                longitude=point.longitude,
                accuracy_meters=point.accuracy_meters,
                recorded_at=point.recorded_at,
            )
        )

    add_field_data_event(
        db=db,
        tenant_id=tenant.id,
        event_type="treatment_session.completed",
        entity_type="treatment_session",
        entity_id=treatment_session.id,
        payload={
            "job_id": job.id,
            "treatment_session_id": treatment_session.id,
            **crm_reference_payload(job),
            "gps_point_count": len(payload.gps_points),
            "duration_seconds": treatment_session.duration_seconds,
            "distance_meters": treatment_session.distance_meters,
            "crm_completion_action": "road/changeactivitystate?action=end",
        },
    )
    job.status = JobStatus.COMPLETED
    db.commit()

    saved_session = db.scalar(
        select(TreatmentSession)
        .options(selectinload(TreatmentSession.gps_points))
        .where(TreatmentSession.id == treatment_session.id, TreatmentSession.tenant_id == tenant.id)
    )
    if saved_session is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Treatment session was not saved")
    return saved_session


@router.post(
    "/integrations/crm/treatment-started",
    response_model=CrmTreatmentStartedResponse,
    tags=["integrations"],
)
def receive_crm_treatment_started(
    payload: CrmTreatmentStartedEvent,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
) -> CrmTreatmentStartedResponse:
    job = find_job_for_crm_event(db, tenant, payload)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CRM route stop was not found")

    job.status = JobStatus.IN_PROGRESS
    job.crm_treatment_started_at = payload.started_at
    if payload.road_id is not None:
        job.external_road_id = payload.road_id
    if payload.road_customer_id is not None:
        job.external_road_customer_id = payload.road_customer_id
    if payload.road_customer_order is not None:
        job.external_road_customer_order = payload.road_customer_order
    if payload.activity_ids:
        job.external_activity_ids = payload.activity_ids
    if payload.customer_id is not None:
        job.external_customer_id = payload.customer_id
    if payload.technician_user_id is not None:
        job.external_technician_id = payload.technician_user_id

    add_field_data_event(
        db=db,
        tenant_id=tenant.id,
        event_type="crm.treatment_started",
        entity_type="job",
        entity_id=job.id,
        payload={
            "job_id": job.id,
            **crm_reference_payload(job),
            "crm_treatment_started_at": payload.started_at.isoformat(),
            "technician_email": payload.technician_email,
        },
    )
    db.commit()
    db.refresh(job)

    return CrmTreatmentStartedResponse(
        job_id=job.id,
        status=job.status,
        source_system=job.source_system,
        external_job_id=job.external_job_id,
        road_id=job.external_road_id,
        road_customer_id=job.external_road_customer_id,
        road_customer_order=job.external_road_customer_order,
        activity_ids=job.external_activity_ids,
        crm_treatment_started_at=job.crm_treatment_started_at,
    )
