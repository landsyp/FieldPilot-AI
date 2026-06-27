from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app
from app.models import Customer, Job, JobStatus, Property, ServiceType, Technician, Tenant


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as session:
        seed_test_data(session)
        yield session

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def seed_test_data(session: Session) -> None:
    tenant = Tenant(id=1, name="Vision Gazon", slug="vision-gazon")
    technician = Technician(id=1, tenant_id=1, name="Alex Technician", email="tech.one@example.com")
    customer = Customer(id=1, tenant_id=1, name="Marie Tremblay", phone="514-555-0101")
    property_record = Property(
        id=1,
        tenant_id=1,
        customer_id=1,
        address_line1="124 Rue des Erables",
        city="Laval",
        region="QC",
        postal_code="H7A 1A1",
        country="Canada",
    )
    job = Job(
        id=1,
        tenant_id=1,
        customer_id=1,
        property_id=1,
        technician_id=1,
        scheduled_date=date.today(),
        service_type=ServiceType.FERTILIZER,
        status=JobStatus.SCHEDULED,
        source_system="vision_gazon_crm",
        external_job_id="VG-R3124-RC58355-20260406",
        external_road_id=3124,
        external_road_customer_id=58355,
        external_road_customer_order=3,
        external_activity_ids=[226282],
        external_customer_id=12854,
        external_technician_id=58,
        service_name="Traitement 1 / 1st Treatment",
    )
    session.add_all([tenant, technician, customer, property_record, job])
    session.commit()
