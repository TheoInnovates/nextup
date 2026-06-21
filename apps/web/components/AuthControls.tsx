"use client";

import { useAuth } from "react-oidc-context";

/** Sign in / sign out control reflecting the current OIDC session. */
export function AuthControls() {
  const auth = useAuth();

  if (auth.isLoading) {
    return <span className="text-sm text-neutral-500">…</span>;
  }

  if (auth.isAuthenticated) {
    const name =
      auth.user?.profile.name ?? auth.user?.profile.preferred_username ?? "You";
    return (
      <div className="flex items-center gap-3 text-sm">
        <span className="text-neutral-700">{name}</span>
        <button
          type="button"
          onClick={() => void auth.signoutRedirect()}
          className="rounded border border-neutral-300 px-3 py-1 font-medium text-neutral-700 hover:bg-neutral-100"
        >
          Sign out
        </button>
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={() => void auth.signinRedirect()}
      className="rounded bg-court px-3 py-1 text-sm font-medium text-white hover:bg-court-dark"
    >
      Sign in
    </button>
  );
}
