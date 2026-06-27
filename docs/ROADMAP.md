# FieldPilot AI Roadmap

## MVP

- Multi-tenant repository structure
- Seed Vision Gazon as Tenant #1
- Technician job list for today's scheduled work
- Job detail page with customer, address, service type, and technician
- Browser GPS treatment tracking
- Treatment duration, distance, path, and completion summary
- Backend persistence for treatment sessions and GPS points
- Vision Gazon CRM route-stop identifiers and treatment-start webhook
- Field-data event outbox for future AI intake
- Basic tests and local PostgreSQL setup

## Next

- Authentication and tenant membership
- Technician assignment filtering by logged-in user
- Job status transitions for CRM start, GPS tracking, pause, resume, complete, and CRM completion sync
- Authenticated Vision Gazon CRM connector for start/end callbacks
- Map provider integration for treatment path display
- Alembic migrations
- Admin dashboard for tenants, users, customers, properties, and jobs

## Later

- DJI Osmo video upload
- Drone flight and mapping data ingestion
- AI weed detection pipeline
- Coverage verification engine
- Customer-facing treatment reports
- Billing, subscriptions, and audit logs

## Out of Scope for MVP

- AI model inference
- Drone workflows
- Video upload
- Customer portals
- Production authentication
