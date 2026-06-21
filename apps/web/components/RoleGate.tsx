"use client";

import type { ReactNode } from "react";
import { useAuth } from "react-oidc-context";

import { rolesFromAccessToken } from "@/lib/roles";

/**
 * UX-only role gate: renders `children` if the signed-in user has any of the
 * required roles, otherwise `fallback`. Backend authorization is the real
 * authority — this only controls what the UI offers.
 */
export function RoleGate({
  anyOf,
  children,
  fallback = null,
}: {
  anyOf: string[];
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const auth = useAuth();
  const roles = rolesFromAccessToken(auth.user?.access_token);
  const allowed = roles.some((role) => anyOf.includes(role));
  return <>{allowed ? children : fallback}</>;
}
