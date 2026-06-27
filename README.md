# FieldPilot AI

FieldPilot AI is a multi-tenant SaaS platform for lawn care field operations. This MVP focuses on technician job execution: viewing today's assigned jobs, starting GPS treatment tracking, stopping the treatment, reviewing the route summary, and saving the treatment session through the backend API.

This repository is intentionally prepared for future DJI Osmo video upload, drone mapping, AI weed detection, coverage verification, and customer reporting workflows, but those features are not implemented in this MVP.

Treatment start is modeled as a CRM-origin event. For the local seed tenant, Vision Gazon CRM is represented by `source_system=vision_gazon_crm` and maps FieldPilot jobs to CRM route stops: `road_id`, `road_customer_id`, `road_customer_order`, and one or more CRM `activity_id` values.

## Monorepo

- `frontend` - Next.js 15, TypeScript, Tailwind CSS, shadcn/ui-ready technician interface
- `backend` - FastAPI, SQLAlchemy, PostgreSQL-ready REST API
- `docs` - architecture, API, database, and roadmap notes
- `docker-compose.yml` - local PostgreSQL service

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker Desktop or compatible Docker runtime

## Local Setup

### 1. Start PostgreSQL

```bash
cp .env.example .env
docker compose up -d postgres
```

### 2. Configure and seed the backend

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m seeds.seed
uvicorn app.main:app --reload
```

The seed creates Tenant #1 as Vision Gazon, one technician, sample customers, properties, and today's jobs.

### 3. Start the frontend

```bash
cd frontend
cp .env.example.local .env.local
npm install
npm run dev
```

Open `http://localhost:3000/jobs/today`.

## Tests

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm test
```

## Tenant Model

All operational records are tenant-scoped. The API resolves the active tenant from the `X-Tenant-Slug` header. The frontend defaults to `vision-gazon` for local seed data through `NEXT_PUBLIC_TENANT_SLUG`, but the application is not branded or hardcoded for Vision Gazon.

## CRM and Future AI Data Flow

- Vision Gazon CRM starts treatments from `RoadController::changeActivityState`, which calls `Road::changeActivityState("start", road_id, order, technician_id)`.
- CRM systems notify FieldPilot through `POST /api/integrations/crm/treatment-started`.
- The technician app records GPS tracking only after the CRM treatment start.
- Completed treatment sessions write a `field_data_events` outbox record.
- Future AI workers should consume `field_data_events`, not call the technician app directly.

## MVP Flow

1. Technician opens today's jobs.
2. Technician opens a job.
3. Job page shows customer, property address, service type, and technician.
4. Technician starts the treatment in the CRM.
5. FieldPilot receives the CRM treatment-start event and unlocks GPS tracking.
6. Technician starts GPS tracking and the browser captures points every second.
7. Technician stops tracking.
8. The UI shows duration, distance walked, GPS path, and completion status.
9. The frontend saves the treatment session through the backend API.
