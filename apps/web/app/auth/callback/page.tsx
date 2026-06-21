"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "react-oidc-context";

/**
 * OIDC redirect target. `react-oidc-context` processes the `code`/`state` query
 * params automatically on load; once authenticated we send the user home.
 */
export default function AuthCallbackPage() {
  const auth = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (auth.isAuthenticated) {
      router.replace("/");
    }
  }, [auth.isAuthenticated, router]);

  if (auth.error) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6 text-center">
        <p role="alert" className="font-medium text-red-600">
          Sign-in failed: {auth.error.message}
        </p>
        <Link href="/" className="text-court underline">
          Return home
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 text-center">
      <p role="status" className="text-neutral-500">
        Signing you in…
      </p>
    </main>
  );
}
