"use client";

import Link from "next/link";

import { RoleGate } from "@/components/RoleGate";
import { RunList } from "@/components/RunList";

/** Runs index: list runs; organizers/admins get a "New run" action. */
export default function RunsPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <header className="flex items-center justify-between gap-4">
        <div>
          <Link href="/" className="text-sm text-court hover:underline">
            ← Home
          </Link>
          <h1 className="mt-1 text-2xl font-bold tracking-tight">Runs</h1>
        </div>
        <RoleGate anyOf={["organizer", "admin"]}>
          <Link
            href="/runs/new"
            className="rounded bg-court px-4 py-2 text-sm font-medium text-white hover:bg-court-dark"
          >
            New run
          </Link>
        </RoleGate>
      </header>

      <RunList />
    </main>
  );
}
