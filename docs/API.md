# API

Base URL for local development:

```text
http://localhost:8000
```

Tenant context is passed with:

```http
X-Tenant-Slug: vision-gazon
```

## Health

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

## List Today's Jobs

```http
GET /api/jobs/today
```

Optional query parameters:

- `service_date` - `YYYY-MM-DD`
- `technician_id` - integer

Response:

```json
[
  {
    "id": 1,
	    "scheduled_date": "2026-06-27",
	    "service_type": "fertilizer",
	    "service_name": "Traitement 1 / 1st Treatment",
	    "status": "scheduled",
	    "source_system": "vision_gazon_crm",
	    "external_job_id": "VG-R3124-RC58355-20260406",
	    "external_road_id": 3124,
	    "external_road_customer_id": 58355,
	    "external_road_customer_order": 3,
	    "external_activity_ids": [226282],
	    "external_customer_id": 12854,
	    "external_technician_id": 58,
	    "crm_treatment_started_at": null,
	    "customer": {
      "id": 1,
      "name": "Marie Tremblay",
      "phone": "514-555-0101"
    },
    "property": {
      "id": 1,
      "address_line1": "124 Rue des Erables",
      "city": "Laval",
      "region": "QC",
      "postal_code": "H7A 1A1",
      "country": "Canada"
    },
    "technician": {
      "id": 1,
      "name": "Alex Technician",
      "email": "tech.one@visiongazon.example"
    },
	    "notes": "Vision Gazon CRM road #3124, stop #3. Front and back lawn treatment."
  }
]
```

## Get Job

```http
GET /api/jobs/{job_id}
```

Returns one tenant-scoped job with customer, property, and technician details.

Job responses include CRM origin fields:

- `source_system`
- `external_job_id`
- `external_road_id`
- `external_road_customer_id`
- `external_road_customer_order`
- `external_activity_ids`
- `external_customer_id`
- `external_technician_id`
- `crm_treatment_started_at`

## CRM Treatment Started

```http
POST /api/integrations/crm/treatment-started
```

This endpoint records that the tenant CRM started the treatment. For the seed tenant, Vision Gazon CRM uses `source_system=vision_gazon_crm`. Its local CRM flow is `road/changeactivitystate`, which maps to `Road::changeActivityState("start", road_id, order, technician_id)`.

Request:

```json
{
  "source_system": "vision_gazon_crm",
  "road_id": 3124,
  "road_customer_id": 58355,
  "road_customer_order": 3,
  "activity_ids": [226282],
  "customer_id": 12854,
  "technician_user_id": 58,
  "started_at": "2026-06-27T14:00:00Z",
  "technician_email": "tech.one@visiongazon.example"
}
```

Response:

```json
{
  "job_id": 1,
  "status": "in_progress",
  "source_system": "vision_gazon_crm",
  "external_job_id": "VG-R3124-RC58355-20260406",
  "road_id": 3124,
  "road_customer_id": 58355,
  "road_customer_order": 3,
  "activity_ids": [226282],
  "crm_treatment_started_at": "2026-06-27T14:00:00Z"
}
```

## Create Treatment Session

```http
POST /api/jobs/{job_id}/treatment-sessions
```

Request:

For Vision Gazon CRM-origin jobs, this request is accepted only after the matching CRM treatment-start event has been received.

```json
{
  "technician_id": 1,
  "started_at": "2026-06-27T14:00:00Z",
  "stopped_at": "2026-06-27T14:08:30Z",
  "completion_status": "completed",
  "gps_points": [
    {
      "sequence": 0,
      "latitude": 45.5019,
      "longitude": -73.5674,
      "accuracy_meters": 6,
      "recorded_at": "2026-06-27T14:00:00Z"
    }
  ]
}
```

Response:

```json
{
  "id": 1,
  "job_id": 1,
  "technician_id": 1,
  "started_at": "2026-06-27T14:00:00Z",
  "stopped_at": "2026-06-27T14:08:30Z",
  "duration_seconds": 510,
  "distance_meters": 124.5,
  "completion_status": "completed",
  "gps_points": []
}
```

The backend validates tenant scope, verifies the technician is assigned to the job, stores ordered GPS points, computes duration and distance, marks the job completed, and writes a `treatment_session.completed` field-data event for the future AI pipeline.
