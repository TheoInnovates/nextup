import Link from "next/link";

import { AuthControls } from "@/components/AuthControls";
import { HealthStatus } from "@/components/HealthStatus";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-6 px-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">NextUp 🏀</h1>
          <p className="mt-2 text-neutral-600">
            Scheduling for pickup basketball runs — know when to arrive and when
            you&apos;ll play.
          </p>
          <nav className="mt-3 flex gap-4">
            <Link href="/gyms" className="font-medium text-court hover:underline">
              Browse gyms →
            </Link>
            <Link href="/runs" className="font-medium text-court hover:underline">
              Browse runs →
            </Link>
            <Link
              href="/notifications"
              className="font-medium text-court hover:underline"
            >
              Notifications →
            </Link>
          </nav>
        </div>
        <AuthControls />
      </header>
      <section className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-neutral-500">
          Backend connectivity
        </h2>
        <HealthStatus />
      </section>
    </main>
  );
}
