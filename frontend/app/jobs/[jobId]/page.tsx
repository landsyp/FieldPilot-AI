import { JobTreatmentScreen } from "@/app/jobs/[jobId]/job-treatment-screen";

export default async function JobPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  return <JobTreatmentScreen jobId={Number(jobId)} />;
}
