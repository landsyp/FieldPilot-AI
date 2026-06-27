# Database

The backend uses SQLAlchemy models and is PostgreSQL-ready through `DATABASE_URL`.

## Local Database

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Backend default:

```bash
DATABASE_URL=postgresql+psycopg://fieldpilot:fieldpilot@localhost:5432/fieldpilot
```

For quick local experiments, the backend can fall back to SQLite when `DATABASE_URL` is not set.

## Core Tables

### tenants

SaaS tenant record. Vision Gazon is seeded as Tenant #1 for local development.

### technicians

Tenant-scoped technicians who can be assigned jobs and treatment sessions.

### customers

Tenant-scoped customers.

### properties

Tenant-scoped service properties linked to customers.

### jobs

Tenant-scoped scheduled service work. Each job links to customer, property, technician, service type, exact CRM service name, date, and status.

CRM-origin fields:

- `source_system` - source CRM key such as `vision_gazon_crm`
- `external_job_id` - external route-stop identifier such as `VG-R3124-RC58355-20260406`
- `external_road_id` - Vision Gazon CRM `road.road_id`
- `external_road_customer_id` - Vision Gazon CRM `road_customer.road_customer_id`
- `external_road_customer_order` - Vision Gazon CRM `road_customer.road_customer_order`
- `external_activity_ids` - Vision Gazon CRM `activity.activity_id` values linked through `road_customer_activity`
- `external_customer_id` - Vision Gazon CRM `customer.customer_id`
- `external_technician_id` - Vision Gazon CRM `user.user_id`
- `crm_treatment_started_at` - time the CRM marked the treatment as started

Service types:

- `fertilizer`
- `weed_control`

Job statuses:

- `scheduled`
- `in_progress`
- `completed`

### treatment_sessions

Completed field execution record for a job. Stores technician, start/stop times, duration, distance, and completion status.

### gps_points

Ordered GPS point samples captured by the technician browser during treatment.

### field_data_events

Tenant-scoped outbox table for downstream processing. Future AI, coverage verification, report generation, and media processing workers should consume this table after operational data is validated and stored.

Current events include `crm.treatment_started` and `treatment_session.completed`. The completion payload includes CRM route-stop identifiers so a future connector can call Vision Gazon CRM's end-treatment path and future AI can associate GPS data with the original CRM activities.

## Migration Plan

The MVP creates tables from SQLAlchemy metadata for speed. Before production, add Alembic migrations and enforce migrations in deployment.

## Tenant Isolation

Operational tables include `tenant_id`. API queries must always filter by the resolved tenant. Future production hardening should add authenticated tenant memberships and authorization checks.
