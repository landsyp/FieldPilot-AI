from datetime import date

from sqlalchemy import select

from app import models  # noqa: F401
from app.db.database import Base, SessionLocal, engine
from app.models import Customer, Job, JobStatus, Property, ServiceType, Technician, Tenant


def seed() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        tenant = db.scalar(select(Tenant).where(Tenant.slug == "vision-gazon"))
        if tenant is None:
            tenant = Tenant(id=1, name="Vision Gazon", slug="vision-gazon")
            db.add(tenant)
            db.flush()

        technician = db.scalar(
            select(Technician).where(
                Technician.tenant_id == tenant.id,
                Technician.email == "tech.one@visiongazon.example",
            )
        )
        if technician is None:
            technician = Technician(
                tenant_id=tenant.id,
                name="Alex Technician",
                email="tech.one@visiongazon.example",
            )
            db.add(technician)
            db.flush()

        existing_today_jobs = db.scalars(
            select(Job).where(
                Job.tenant_id == tenant.id,
                Job.scheduled_date == date.today(),
            )
        ).all()
        if existing_today_jobs:
            db.commit()
            print("Seed data already exists.")
            return

        customer_one = Customer(tenant_id=tenant.id, name="Marie Tremblay", phone="514-555-0101")
        customer_two = Customer(tenant_id=tenant.id, name="Noah Gagnon", phone="514-555-0124")
        db.add_all([customer_one, customer_two])
        db.flush()

        property_one = Property(
            tenant_id=tenant.id,
            customer_id=customer_one.id,
            address_line1="124 Rue des Erables",
            city="Laval",
            region="QC",
            postal_code="H7A 1A1",
            country="Canada",
        )
        property_two = Property(
            tenant_id=tenant.id,
            customer_id=customer_two.id,
            address_line1="88 Avenue du Parc",
            city="Longueuil",
            region="QC",
            postal_code="J4K 2B2",
            country="Canada",
        )
        db.add_all([property_one, property_two])
        db.flush()

        db.add_all(
            [
                Job(
                    tenant_id=tenant.id,
                    customer_id=customer_one.id,
                    property_id=property_one.id,
                    technician_id=technician.id,
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
                    service_name="Traitement 1 / 1st Treatment",
                    notes="Vision Gazon CRM road #3124, stop #3. Front and back lawn treatment.",
                ),
                Job(
                    tenant_id=tenant.id,
                    customer_id=customer_two.id,
                    property_id=property_two.id,
                    technician_id=technician.id,
                    scheduled_date=date.today(),
                    service_type=ServiceType.WEED_CONTROL,
                    status=JobStatus.SCHEDULED,
                    source_system="vision_gazon_crm",
                    external_job_id="VG-R3124-RC58356-20260406",
                    external_road_id=3124,
                    external_road_customer_id=58356,
                    external_road_customer_order=4,
                    external_activity_ids=[230788, 228063],
                    external_customer_id=10383,
                    service_name="Chiendent - Crabgrass, Traitement 1 / 1st Treatment",
                    notes="Vision Gazon CRM road #3124, stop #4. Spot treatment near driveway edge.",
                ),
            ]
        )
        db.commit()
        print("Seeded Vision Gazon tenant, one technician, and sample jobs.")


if __name__ == "__main__":
    seed()
