export type ServiceType = "fertilizer" | "weed_control";
export type JobStatus = "scheduled" | "in_progress" | "completed";
export type CompletionStatus = "completed" | "incomplete";

export interface Customer {
  id: number;
  name: string;
  phone: string | null;
}

export interface ServiceProperty {
  id: number;
  address_line1: string;
  city: string;
  region: string;
  postal_code: string;
  country: string;
}

export interface Technician {
  id: number;
  name: string;
  email: string;
}

export interface Job {
  id: number;
  scheduled_date: string;
  service_type: ServiceType;
  service_name: string | null;
  status: JobStatus;
  source_system: string;
  external_job_id: string | null;
  external_road_id: number | null;
  external_road_customer_id: number | null;
  external_road_customer_order: number | null;
  external_activity_ids: number[];
  external_customer_id: number | null;
  external_technician_id: number | null;
  crm_treatment_started_at: string | null;
  customer: Customer;
  property: ServiceProperty;
  technician: Technician;
  notes: string | null;
}

export interface GpsPoint {
  sequence: number;
  latitude: number;
  longitude: number;
  accuracy_meters: number | null;
  recorded_at: string;
}

export interface TreatmentSessionPayload {
  technician_id: number;
  started_at: string;
  stopped_at: string;
  completion_status: CompletionStatus;
  gps_points: GpsPoint[];
}

export interface TreatmentSession {
  id: number;
  job_id: number;
  technician_id: number;
  started_at: string;
  stopped_at: string;
  duration_seconds: number;
  distance_meters: number;
  completion_status: CompletionStatus;
  gps_points: Array<GpsPoint & { id: number }>;
}
