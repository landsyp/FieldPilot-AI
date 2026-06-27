"use client";

import { AlertTriangle, CheckCircle2, Loader2, MapPin, RefreshCcw, Sprout, UserRound } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getTodayJobs } from "@/lib/api";
import type { Job, JobStatus, ServiceType } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

const serviceLabels: Record<ServiceType, string> = {
  fertilizer: "Fertilizer",
  weed_control: "Weed control",
};

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
  return references.join(" · ");
}

const statusLabels: Record<JobStatus, string> = {
  scheduled: "Scheduled",
  in_progress: "In progress",
  completed: "Completed",
};

function formatSourceSystem(sourceSystem: string) {
  return sourceSystem
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function TodayJobsScreen() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const todayLabel = useMemo(
    () =>
      new Intl.DateTimeFormat(undefined, {
        weekday: "long",
        month: "short",
        day: "numeric",
      }).format(new Date()),
    [],
  );

  async function loadJobs() {
    setIsLoading(true);
    setError(null);
    try {
      setJobs(await getTodayJobs());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load jobs.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadJobs();
  }, []);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-2xl flex-col px-4 py-5 sm:px-6">
      <header className="mb-5 flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-muted-foreground">FieldPilot AI</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-normal">Today&apos;s jobs</h1>
          <p className="mt-1 text-sm text-muted-foreground">{todayLabel}</p>
        </div>
        <Button variant="outline" size="icon" onClick={loadJobs} disabled={isLoading} aria-label="Refresh jobs">
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCcw className="h-4 w-4" />}
        </Button>
      </header>

      {error ? (
        <div className="mb-4 flex items-start gap-3 rounded-lg border border-destructive/30 bg-white p-4 text-sm text-destructive">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>{error}</p>
        </div>
      ) : null}

      {isLoading ? (
        <div className="flex flex-1 items-center justify-center text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading jobs
        </div>
      ) : jobs.length === 0 ? (
        <div className="rounded-lg border bg-white p-6 text-center">
          <CheckCircle2 className="mx-auto h-8 w-8 text-primary" />
          <h2 className="mt-3 text-lg font-semibold">No jobs scheduled</h2>
          <p className="mt-1 text-sm text-muted-foreground">New assignments will appear here when they are ready.</p>
        </div>
      ) : (
        <section className="grid gap-3">
          {jobs.map((job) => (
            <Card key={job.id} className="overflow-hidden">
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <CardTitle>{job.customer.name}</CardTitle>
                    <p className="mt-1 flex items-start gap-2 text-sm text-muted-foreground">
                      <MapPin className="mt-0.5 h-4 w-4 shrink-0" />
                      <span>
                        {job.property.address_line1}, {job.property.city}
                      </span>
                    </p>
                  </div>
                  <Badge variant={job.status === "completed" ? "success" : "outline"}>{statusLabels[job.status]}</Badge>
                </div>
              </CardHeader>
              <CardContent className="grid gap-2 text-sm">
                <div className="flex items-center gap-2">
                  <Sprout className="h-4 w-4 text-primary" />
                  <span>{formatService(job)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <UserRound className="h-4 w-4 text-accent" />
                  <span>{job.technician.name}</span>
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatSourceSystem(job.source_system)}
                  {formatCrmReference(job) ? ` - ${formatCrmReference(job)}` : ""}
                </div>
              </CardContent>
              <CardFooter>
                <Button asChild className="w-full" size="lg">
                  <Link href={`/jobs/${job.id}`}>Open job</Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </section>
      )}
    </main>
  );
}
