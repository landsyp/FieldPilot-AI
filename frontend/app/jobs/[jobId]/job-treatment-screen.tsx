"use client";

import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  Database,
  Loader2,
  MapPin,
  Play,
  Route,
  Square,
  Sprout,
  UserRound,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getJob, saveTreatmentSession } from "@/lib/api";
import { calculateDistanceMeters, formatDuration } from "@/lib/geo";
import type { GpsPoint, Job, ServiceType, TreatmentSession } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const serviceLabels: Record<ServiceType, string> = {
  fertilizer: "Fertilizer",
  weed_control: "Weed control",
};

function formatSourceSystem(sourceSystem: string) {
  return sourceSystem
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatService(job: Job) {
  return job.service_name || serviceLabels[job.service_type];
}

function formatCrmReference(job: Job) {
  const references: string[] = [];
  if (job.external_job_id) {
    references.push(job.external_job_id);
  }
  if (job.external_road_id) {
    references.push(`Road #${job.external_road_id}`);
  }
  if (job.external_road_customer_order) {
    references.push(`Stop #${job.external_road_customer_order}`);
  }
  if (job.external_activity_ids.length > 0) {
    references.push(`Activities ${job.external_activity_ids.join(", ")}`);
  }
  return references.join(" · ");
}

export function JobTreatmentScreen({ jobId }: { jobId: number }) {
  const [job, setJob] = useState<Job | null>(null);
  const [points, setPoints] = useState<GpsPoint[]>([]);
  const [startedAt, setStartedAt] = useState<Date | null>(null);
  const [stoppedAt, setStoppedAt] = useState<Date | null>(null);
  const [isTracking, setIsTracking] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">("idle");
  const [savedSession, setSavedSession] = useState<TreatmentSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);
  const sequenceRef = useRef(0);

  const durationSeconds = useMemo(() => {
    if (!startedAt) {
      return 0;
    }
    const endTime = stoppedAt ?? new Date();
    return Math.max(0, Math.floor((endTime.getTime() - startedAt.getTime()) / 1000));
  }, [startedAt, stoppedAt, points.length]);

  const distanceMeters = useMemo(() => calculateDistanceMeters(points), [points]);

  const capturePoint = useCallback(() => {
    if (!("geolocation" in navigator)) {
      setError("GPS is not available in this browser.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const point: GpsPoint = {
          sequence: sequenceRef.current,
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy_meters: position.coords.accuracy ?? null,
          recorded_at: new Date().toISOString(),
        };
        sequenceRef.current += 1;
        setPoints((currentPoints) => [...currentPoints, point]);
      },
      (positionError) => {
        setError(positionError.message || "Unable to read GPS location.");
      },
      {
        enableHighAccuracy: true,
        maximumAge: 0,
        timeout: 10000,
      },
    );
  }, []);

  useEffect(() => {
    async function loadJob() {
      setIsLoading(true);
      setError(null);
      try {
        setJob(await getJob(jobId));
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Unable to load this job.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadJob();
  }, [jobId]);

  useEffect(() => {
    return () => {
      if (intervalRef.current !== null) {
        window.clearInterval(intervalRef.current);
      }
    };
  }, []);

  function startTreatment() {
    if (!job) {
      return;
    }
    if (!("geolocation" in navigator)) {
      setError("GPS is not available in this browser.");
      return;
    }

    sequenceRef.current = 0;
    setError(null);
    setPoints([]);
    setSavedSession(null);
    setSaveState("idle");
    setStartedAt(new Date());
    setStoppedAt(null);
    setIsTracking(true);
    capturePoint();
    intervalRef.current = window.setInterval(capturePoint, 1000);
  }

  async function stopTreatment() {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsTracking(false);

    const stopTime = new Date();
    setStoppedAt(stopTime);

    if (!job || !startedAt) {
      return;
    }
    if (points.length === 0) {
      setError("No GPS points were captured. Check location permission and try again.");
      return;
    }

    setSaveState("saving");
    setError(null);
    try {
      const treatmentStartedAt = job.crm_treatment_started_at ? new Date(job.crm_treatment_started_at) : startedAt;
      const session = await saveTreatmentSession(job.id, {
        technician_id: job.technician.id,
        started_at: treatmentStartedAt.toISOString(),
        stopped_at: stopTime.toISOString(),
        completion_status: "completed",
        gps_points: points,
      });
      setSavedSession(session);
      setSaveState("saved");
      setJob({ ...job, status: "completed" });
    } catch (requestError) {
      setSaveState("idle");
      setError(requestError instanceof Error ? requestError.message : "Unable to save treatment session.");
    }
  }

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Loading job
      </main>
    );
  }

  if (!job) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-2xl flex-col px-4 py-5">
        <Button asChild variant="ghost" className="mb-4 w-fit pl-0">
          <Link href="/jobs/today">
            <ArrowLeft className="h-4 w-4" />
            Jobs
          </Link>
        </Button>
        <div className="rounded-lg border bg-white p-5 text-sm text-destructive">{error ?? "Job not found."}</div>
      </main>
    );
  }

  const waitingForCrmStart = job.source_system === "vision_gazon_crm" && !job.crm_treatment_started_at;
  const crmReference = formatCrmReference(job);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-2xl flex-col px-4 py-5 sm:px-6">
      <Button asChild variant="ghost" className="mb-4 w-fit pl-0">
        <Link href="/jobs/today">
          <ArrowLeft className="h-4 w-4" />
          Jobs
        </Link>
      </Button>

      <header className="mb-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Job #{job.id}</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-normal">{job.customer.name}</h1>
          </div>
          <Badge variant={job.status === "completed" ? "success" : "outline"}>{job.status.replace("_", " ")}</Badge>
        </div>
      </header>

      {error ? (
        <div className="mb-4 flex items-start gap-3 rounded-lg border border-destructive/30 bg-white p-4 text-sm text-destructive">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>{error}</p>
        </div>
      ) : null}

      <section className="grid gap-3">
        <Card>
          <CardHeader>
            <CardTitle>Job details</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm">
            <Detail icon={<MapPin className="h-4 w-4" />} label="Property">
              {job.property.address_line1}, {job.property.city}, {job.property.region} {job.property.postal_code}
            </Detail>
            <Detail icon={<Sprout className="h-4 w-4" />} label="Service">
              {formatService(job)}
            </Detail>
            <Detail icon={<UserRound className="h-4 w-4" />} label="Technician">
              {job.technician.name}
            </Detail>
            <Detail icon={<Database className="h-4 w-4" />} label="CRM source">
              {formatSourceSystem(job.source_system)}
              {crmReference ? ` - ${crmReference}` : ""}
            </Detail>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <CardTitle>Treatment tracking</CardTitle>
              {isTracking ? <Badge variant="secondary">Tracking</Badge> : null}
            </div>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="rounded-lg border bg-muted/35 p-3 text-sm">
              <p className="text-xs font-medium uppercase text-muted-foreground">Treatment start source</p>
              <p className="mt-1 font-medium">
                {job.crm_treatment_started_at
                  ? new Intl.DateTimeFormat(undefined, {
                      hour: "numeric",
                      minute: "2-digit",
                      second: "2-digit",
                    }).format(new Date(job.crm_treatment_started_at))
                  : waitingForCrmStart
                    ? "Waiting for Vision Gazon CRM start"
                    : `${formatSourceSystem(job.source_system)} pending`}
              </p>
              {waitingForCrmStart ? (
                <p className="mt-1 text-xs text-muted-foreground">
                  Start the route stop in Vision Gazon CRM first, then GPS tracking unlocks here.
                </p>
              ) : null}
            </div>
            <div className="grid grid-cols-3 gap-2">
              <Metric icon={<Clock3 className="h-4 w-4" />} label="Duration" value={formatDuration(durationSeconds)} />
              <Metric icon={<Route className="h-4 w-4" />} label="Distance" value={`${Math.round(distanceMeters)} m`} />
              <Metric icon={<MapPin className="h-4 w-4" />} label="Points" value={String(points.length)} />
            </div>

            <TreatmentPath points={points} />

            {isTracking ? (
              <Button variant="destructive" size="lg" onClick={stopTreatment}>
                <Square className="h-4 w-4" />
                Stop treatment
              </Button>
            ) : (
              <Button size="lg" onClick={startTreatment} disabled={saveState === "saving" || waitingForCrmStart}>
                <Play className="h-4 w-4" />
                {waitingForCrmStart ? "Start in Vision Gazon CRM first" : "Start GPS tracking"}
              </Button>
            )}
          </CardContent>
        </Card>

        {stoppedAt ? (
          <Card>
            <CardHeader>
              <CardTitle>Job summary</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 text-sm">
              <SummaryRow label="Duration" value={formatDuration(savedSession?.duration_seconds ?? durationSeconds)} />
              <SummaryRow
                label="Distance walked"
                value={`${Math.round(savedSession?.distance_meters ?? distanceMeters)} m`}
              />
              <SummaryRow label="GPS path" value={`${savedSession?.gps_points.length ?? points.length} points`} />
              <SummaryRow label="CRM source" value={formatSourceSystem(job.source_system)} />
              {crmReference ? <SummaryRow label="CRM route stop" value={crmReference} /> : null}
              <SummaryRow
                label="Completion status"
                value={saveState === "saved" ? "Completed and saved" : saveState === "saving" ? "Saving" : "Stopped"}
              />
              {saveState === "saved" ? (
                <div className="flex items-center gap-2 rounded-lg bg-emerald-50 p-3 text-emerald-800">
                  <CheckCircle2 className="h-4 w-4" />
                  Session #{savedSession?.id} saved through the API
                </div>
              ) : null}
            </CardContent>
          </Card>
        ) : null}
      </section>
    </main>
  );
}

function Detail({
  icon,
  label,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-3">
      <div className="mt-0.5 text-primary">{icon}</div>
      <div>
        <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
        <p className="mt-0.5 text-foreground">{children}</p>
      </div>
    </div>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-muted/35 p-3">
      <div className="flex items-center gap-1.5 text-muted-foreground">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <p className="mt-2 text-lg font-semibold tracking-normal">{value}</p>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b pb-2 last:border-0 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}

function TreatmentPath({ points }: { points: GpsPoint[] }) {
  if (points.length === 0) {
    return (
      <div className="flex h-44 items-center justify-center rounded-lg border border-dashed bg-muted/30 text-sm text-muted-foreground">
        GPS path will appear here
      </div>
    );
  }

  const width = 320;
  const height = 176;
  const padding = 18;
  const latitudes = points.map((point) => point.latitude);
  const longitudes = points.map((point) => point.longitude);
  const minLatitude = Math.min(...latitudes);
  const maxLatitude = Math.max(...latitudes);
  const minLongitude = Math.min(...longitudes);
  const maxLongitude = Math.max(...longitudes);
  const latitudeRange = maxLatitude - minLatitude || 0.0001;
  const longitudeRange = maxLongitude - minLongitude || 0.0001;

  const normalizedPoints = points.map((point) => ({
    x: padding + ((point.longitude - minLongitude) / longitudeRange) * (width - padding * 2),
    y: height - padding - ((point.latitude - minLatitude) / latitudeRange) * (height - padding * 2),
  }));
  const path = normalizedPoints.map((point) => `${point.x},${point.y}`).join(" ");
  const firstPoint = normalizedPoints[0];
  const lastPoint = normalizedPoints[normalizedPoints.length - 1];

  return (
    <div className="rounded-lg border bg-white p-2">
      <svg className="h-44 w-full" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="GPS treatment path">
        <rect x="0" y="0" width={width} height={height} rx="8" className="fill-muted/30" />
        <polyline points={path} fill="none" stroke="hsl(var(--primary))" strokeWidth="5" strokeLinecap="round" />
        <circle cx={firstPoint.x} cy={firstPoint.y} r="6" className="fill-secondary" />
        <circle cx={lastPoint.x} cy={lastPoint.y} r="6" className="fill-primary" />
      </svg>
    </div>
  );
}
