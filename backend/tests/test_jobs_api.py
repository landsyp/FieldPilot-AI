from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FieldDataEvent


def test_list_today_jobs(client: TestClient) -> None:
    response = client.get("/api/jobs/today", headers={"X-Tenant-Slug": "vision-gazon"})

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["customer"]["name"] == "Marie Tremblay"
    assert jobs[0]["service_type"] == "fertilizer"
    assert jobs[0]["service_name"] == "Traitement 1 / 1st Treatment"
    assert jobs[0]["technician"]["name"] == "Alex Technician"
    assert jobs[0]["source_system"] == "vision_gazon_crm"
    assert jobs[0]["external_job_id"] == "VG-R3124-RC58355-20260406"
    assert jobs[0]["external_road_id"] == 3124
    assert jobs[0]["external_road_customer_id"] == 58355
    assert jobs[0]["external_road_customer_order"] == 3
    assert jobs[0]["external_activity_ids"] == [226282]


def test_create_treatment_session(client: TestClient, db_session: Session) -> None:
    started_at = datetime.now(timezone.utc)
    stopped_at = started_at + timedelta(seconds=3)
    client.post(
        "/api/integrations/crm/treatment-started",
        headers={"X-Tenant-Slug": "vision-gazon"},
        json={
            "source_system": "vision_gazon_crm",
            "road_id": 3124,
            "road_customer_id": 58355,
            "road_customer_order": 3,
            "activity_ids": [226282],
            "started_at": started_at.isoformat(),
            "technician_user_id": 58,
            "technician_email": "tech.one@example.com",
        },
    )
    response = client.post(
        "/api/jobs/1/treatment-sessions",
        headers={"X-Tenant-Slug": "vision-gazon"},
        json={
            "technician_id": 1,
            "started_at": started_at.isoformat(),
            "stopped_at": stopped_at.isoformat(),
            "completion_status": "completed",
            "gps_points": [
                {
                    "sequence": 0,
                    "latitude": 45.5019,
                    "longitude": -73.5674,
                    "accuracy_meters": 6,
                    "recorded_at": started_at.isoformat(),
                },
                {
                    "sequence": 1,
                    "latitude": 45.5024,
                    "longitude": -73.5674,
                    "accuracy_meters": 6,
                    "recorded_at": (started_at + timedelta(seconds=1)).isoformat(),
                },
            ],
        },
    )

    assert response.status_code == 201
    session = response.json()
    assert session["duration_seconds"] == 3
    assert session["distance_meters"] > 0
    assert session["completion_status"] == "completed"
    assert len(session["gps_points"]) == 2

    job_response = client.get("/api/jobs/1", headers={"X-Tenant-Slug": "vision-gazon"})
    assert job_response.json()["status"] == "completed"

    event = db_session.scalar(select(FieldDataEvent).where(FieldDataEvent.event_type == "treatment_session.completed"))
    assert event is not None
    assert event.payload["source_system"] == "vision_gazon_crm"
    assert event.payload["external_job_id"] == "VG-R3124-RC58355-20260406"
    assert event.payload["road_id"] == 3124
    assert event.payload["road_customer_id"] == 58355
    assert event.payload["road_customer_order"] == 3
    assert event.payload["activity_ids"] == [226282]
    assert event.payload["crm_completion_action"] == "road/changeactivitystate?action=end"


def test_rejects_gps_session_before_crm_start(client: TestClient) -> None:
    started_at = datetime.now(timezone.utc)
    response = client.post(
        "/api/jobs/1/treatment-sessions",
        headers={"X-Tenant-Slug": "vision-gazon"},
        json={
            "technician_id": 1,
            "started_at": started_at.isoformat(),
            "stopped_at": (started_at + timedelta(seconds=3)).isoformat(),
            "completion_status": "completed",
            "gps_points": [
                {
                    "sequence": 0,
                    "latitude": 45.5019,
                    "longitude": -73.5674,
                    "accuracy_meters": 6,
                    "recorded_at": started_at.isoformat(),
                }
            ],
        },
    )

    assert response.status_code == 409
    assert "Vision Gazon CRM" in response.json()["detail"]


def test_receive_crm_treatment_started(client: TestClient, db_session: Session) -> None:
    started_at = datetime.now(timezone.utc)
    response = client.post(
        "/api/integrations/crm/treatment-started",
        headers={"X-Tenant-Slug": "vision-gazon"},
        json={
            "source_system": "vision_gazon_crm",
            "road_id": 3124,
            "road_customer_id": 58355,
            "road_customer_order": 3,
            "activity_ids": [226282],
            "customer_id": 12854,
            "started_at": started_at.isoformat(),
            "technician_user_id": 58,
            "technician_email": "tech.one@example.com",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == 1
    assert payload["status"] == "in_progress"
    assert payload["source_system"] == "vision_gazon_crm"
    assert payload["external_job_id"] == "VG-R3124-RC58355-20260406"
    assert payload["road_id"] == 3124
    assert payload["road_customer_id"] == 58355
    assert payload["road_customer_order"] == 3
    assert payload["activity_ids"] == [226282]

    event = db_session.scalar(select(FieldDataEvent).where(FieldDataEvent.event_type == "crm.treatment_started"))
    assert event is not None
    assert event.payload["external_job_id"] == "VG-R3124-RC58355-20260406"
    assert event.payload["road_id"] == 3124
    assert event.payload["road_customer_id"] == 58355
    assert event.payload["road_customer_order"] == 3
    assert event.payload["activity_ids"] == [226282]
    assert event.payload["customer_id"] == 12854
    assert event.payload["technician_user_id"] == 58
