/**
 * Minimal API client.
 *
 * Wraps `fetch` with JSON handling and a typed error. Responses are validated at
 * runtime with Zod (project convention). A bearer token is attached when an auth
 * token provider has been registered (see `setAuthTokenProvider`).
 */
import { z } from "zod";

import { env } from "@/lib/env";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Returns the current OIDC access token, or `null` when unauthenticated. The
 * default is "no token"; the auth layer registers a real provider at runtime via
 * `setAuthTokenProvider`, keeping this module free of any auth/React dependency.
 */
let authTokenProvider: () => string | null = () => null;

/** Register the access-token source used to attach `Authorization` headers. */
export function setAuthTokenProvider(fn: () => string | null): void {
  authTokenProvider = fn;
}

export async function apiFetch<T>(
  path: string,
  schema: z.ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  const token = authTokenProvider();
  const res = await fetch(`${env.apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      // Caller-supplied headers win over the defaults injected above.
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    let code: string | undefined;
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: string; code?: string };
      detail = body.detail ?? detail;
      code = body.code;
    } catch {
      // non-JSON error body; keep the default message
    }
    throw new ApiError(res.status, detail, code);
  }

  // 204 No Content has an empty body; skip JSON parsing. Callers that expect a
  // 204 should validate with `z.void()`, whose parse accepts `undefined`.
  if (res.status === 204) {
    return schema.parse(undefined);
  }

  return schema.parse(await res.json());
}

export const healthSchema = z.object({ status: z.string() });
export type Health = z.infer<typeof healthSchema>;

export function getHealth(): Promise<Health> {
  return apiFetch("/health", healthSchema);
}
