"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { AuthProvider, useAuth } from "react-oidc-context";

import { getAuthConfig, onSigninCallback } from "@/lib/auth";
import { setAuthTokenProvider } from "@/lib/api";

/**
 * Renders children only after mount. `oidc-client-ts` (constructed by
 * `AuthProvider`) touches `window`/`localStorage`, so the auth tree must never
 * execute on the server — otherwise `next build` prerendering crashes.
 */
function ClientOnly({
  children,
  fallback,
}: {
  children: ReactNode;
  fallback: ReactNode;
}) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  return <>{mounted ? children : fallback}</>;
}

/** Bridges the OIDC access token into the (auth-agnostic) API layer. */
function AuthTokenBridge() {
  const auth = useAuth();
  useEffect(() => {
    setAuthTokenProvider(() => auth.user?.access_token ?? null);
  }, [auth.user]);
  return null;
}

/**
 * Builds the OIDC settings in the render body (reads `window`), so the config is
 * computed only once mounted on the client — not when the element tree is created
 * during SSR.
 */
function AuthGate({ children }: { children: ReactNode }) {
  return (
    <AuthProvider {...getAuthConfig()} onSigninCallback={onSigninCallback}>
      <AuthTokenBridge />
      {children}
    </AuthProvider>
  );
}

/** Client-side providers: TanStack Query + OIDC auth (client-only). */
export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            staleTime: 30_000,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ClientOnly fallback={<p className="p-6 text-neutral-500">Loading…</p>}>
        <AuthGate>{children}</AuthGate>
      </ClientOnly>
    </QueryClientProvider>
  );
}
