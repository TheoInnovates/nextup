"use client";

import Link from "next/link";

import { GymList } from "@/components/GymList";
import { RoleGate } from "@/components/RoleGate";

/** Gyms index: list all gyms; organizers/admins get a "New gym" action. */
export default function GymsPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <header className="flex items-center justify-between gap-4">
        <div>
          <Link href="/" className="text-sm text-court hover:underline">
            ← Home
          </Link>
          <h1 className="mt-1 text-2xl font-bold tracking-tight">Gyms</h1>
        </div>
        <RoleGate anyOf={["organizer", "admin"]}>
          <Link
            href="/gyms/new"
            className="rounded bg-court px-4 py-2 text-sm font-medium text-white hover:bg-court-dark"
          >
            New gym
          </Link>
        </RoleGate>
      </header>

      <GymList />
    </main>
  );
}
