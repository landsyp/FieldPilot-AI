# FieldPilot AI Architecture

FieldPilot AI is structured as a multi-tenant SaaS monorepo. The MVP keeps the operational loop small and reliable: technicians see assigned work, capture treatment GPS data in the browser, and persist a completed session through the backend API.

## Applications

### Frontend

- Next.js 15 app router
- TypeScript
- Tailwind CSS
- shadcn/ui-ready structure with `components.json`, `components/ui`, and `lib/utils`
- Mobile-first technician workflow

The frontend reads tenant context from `NEXT_PUBLIC_TENANT_SLUG` and sends it to the API as `X-Tenant-Slug`.

### Backend

- FastAPI REST API
- SQLAlchemy ORM
- PostgreSQL-ready through `DATABASE_URL`
- SQLite fallback for quick local development and tests
- Tenant-scoped operational tables from the start

The backend resolves tenant context per request and filters jobs, technicians, and treatment sessions by tenant.

## MVP Treatment Flow

1. Frontend loads today's jobs from `GET /api/jobs/today`.
2. Technician opens a job with `GET /api/jobs/{job_id}`.
3. Tenant CRM starts the treatment through `POST /api/integrations/crm/treatment-started`.
4. Technician starts GPS tracking in the FieldPilot app.
5. Browser geolocation captures GPS points every second.
6. Technician stops GPS tracking.
7. Frontend calculates a live summary and posts all points to `POST /api/jobs/{job_id}/treatment-sessions`.
8. Backend validates tenant and assigned technician, calculates canonical duration and distance, stores the session and GPS points, marks the job completed, and writes a `field_data_events` record for future processing.

## Multi-Tenant Strategy

All operational data includes `tenant_id`. The API uses `X-Tenant-Slug` to resolve the active tenant, with `vision-gazon` as the local default only because it is seeded as Tenant #1.

Future production hardening should replace the header-only tenant selector with authenticated users, tenant membership, roles, and row-level authorization checks.

## CRM-Origin Treatments

Treatment starts in each tenant's CRM. In local seed data, Vision Gazon jobs use `source_system=vision_gazon_crm` and mirror the local CRM route model:

- `road_id` from the CRM `road` table
- `road_customer_id` and `road_customer_order` from `road_customer`
- one or more `activity_id` values from `road_customer_activity`
- generated order IDs like `VG-R3124-RC58355-20260406`, matching the CRM's OptimoRoute export pattern

The Vision Gazon CRM start action lives in `RoadController::changeActivityState`, which calls `Road::changeActivityState("start", road_id, order, technician_id)`. FieldPilot records that action via `POST /api/integrations/crm/treatment-started` before GPS tracking can be saved.

The current CRM endpoint updates an existing FieldPilot job to `in_progress`. A production integration should authenticate webhooks, verify signatures, support job upsert/sync from the CRM, and send completion back to the CRM's `changeActivityState("end", road_id, order, technician_id)` flow after treatment-session persistence.

## Future AI Data Intake

AI does not receive data from the browser directly. The future AI pipeline should consume backend-owned `field_data_events` records after data is validated and persisted.

Current event types:

- `crm.treatment_started`
- `treatment_session.completed`

Future event types can include:

- `media.osmo_video_uploaded`
- `drone.flight_uploaded`
- `coverage.verification_requested`
- `customer_report.requested`

## Future Architecture Lanes

### DJI Osmo Video Upload

Add object storage for raw media, upload sessions, media metadata, and asynchronous processing jobs. Treatment sessions should be able to reference one or more uploaded media assets.

### Drone Mapping

Add parcel boundaries, drone flight records, orthomosaic artifacts, and map layers. Coverage data should be linked back to jobs and treatment sessions.

### AI Weed Detection

Add model inference jobs that consume images/video frames, store detections, and produce geospatial weed-pressure overlays. Keep model execution asynchronous.

### Coverage Verification

Combine GPS paths, property boundaries, application zones, and service rules into verification reports. This should become a service layer on top of treatment sessions and future mapping data.

### Customer Reports

Generate tenant-branded report artifacts from treatment sessions, GPS paths, photos/video, AI detections, and coverage verification outcomes.
