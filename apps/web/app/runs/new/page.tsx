"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { RoleGate } from "@/components/RoleGate";
import { RunForm } from "@/components/RunForm";
import { useCreateRun } from "@/hooks/useRuns";
import { ApiError } from "@/lib/api";
import type { RunCreate } from "@/lib/runs";

function NotAuthorized() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6 text-center">
      <p role="alert" className="font-medium text-red-600">
        You need an organizer account to create a run.
      </p>
      <Link href="/runs" className="text-court underline">
        Back to runs
      </Link>
    </main>
  );
}

function CreateRunForm() {
  const router = useRouter();
  const createRun = useCreateRun();
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleSubmit(values: RunCreate) {
    setSubmitError(null);
    try {
      const run = await createRun.mutateAsync(values);
      router.push(`/runs/${run.id}`);
    } catch (err) {
      setSubmitError(
        err instanceof ApiError
          ? err.message
          : "Something went wrong. Please try again.",
      );
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <header>
        <Link href="/runs" className="text-sm text-court hover:underline">
          ← Runs
        </Link>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">New run</h1>
      </header>
      <RunForm
        submitLabel="Create run"
        onSubmit={handleSubmit}
        submitError={submitError}
        isSubmitting={createRun.isPending}
      />
    </main>
  );
}

/** Create-run page, gated to organizers/admins (UX only; backend enforces). */
export default function NewRunPage() {
  return (
    <RoleGate anyOf={["organizer", "admin"]} fallback={<NotAuthorized />}>
      <CreateRunForm />
    </RoleGate>
  );
}
