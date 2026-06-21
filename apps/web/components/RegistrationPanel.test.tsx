import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  RegistrationStatusView,
  registrationErrorMessage,
} from "@/components/RegistrationPanel";
import { ApiError } from "@/lib/api";
import { type Registration } from "@/lib/registrations";

const base: Registration = {
  id: "reg-1",
  run_id: "run-1",
  player_user_id: "player-1",
  status: "confirmed",
  queue_position: null,
  assigned_slot_number: 4,
  // 22:00 UTC -> 18:00 (6:00 PM) in America/New_York (EDT, -4 in June).
  assigned_arrival_time: "2026-06-23T21:45:00Z",
  estimated_play_time: "2026-06-23T22:00:00Z",
  registered_at: "2026-06-20T12:30:00Z",
  cancelled_at: null,
  checked_in_at: null,
};

const noop = () => {};

describe("RegistrationStatusView", () => {
  it("shows the confirmed card with a formatted play time in the gym zone", () => {
    render(
      <RegistrationStatusView
        registration={base}
        gymTimeZone="America/New_York"
        onRegister={noop}
        isRegistering={false}
        registerErrorMessage={null}
      />,
    );
    expect(screen.getByText(/you're confirmed/i)).toBeInTheDocument();
    // U+202F narrow no-break space before AM/PM in Node 22 ICU — match loosely.
    expect(screen.getByText(/6:00\s*PM/)).toBeInTheDocument();
    expect(screen.getByText(/#4/)).toBeInTheDocument();
  });

  it("shows the register button when not registered", async () => {
    const onRegister = vi.fn();
    render(
      <RegistrationStatusView
        registration={null}
        onRegister={onRegister}
        isRegistering={false}
        registerErrorMessage={null}
      />,
    );
    const button = screen.getByRole("button", { name: /register for this run/i });
    expect(button).toBeInTheDocument();
    await userEvent.click(button);
    expect(onRegister).toHaveBeenCalledOnce();
  });

  it("shows a register error message when present", () => {
    render(
      <RegistrationStatusView
        registration={null}
        onRegister={noop}
        isRegistering={false}
        registerErrorMessage="You're already registered for this run."
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/already registered/i);
  });

  it("shows the queue position when waitlisted", () => {
    render(
      <RegistrationStatusView
        registration={{
          ...base,
          status: "waitlisted",
          queue_position: 3,
          assigned_slot_number: null,
          assigned_arrival_time: null,
          estimated_play_time: null,
        }}
        gymTimeZone="America/New_York"
        onRegister={noop}
        isRegistering={false}
        registerErrorMessage={null}
      />,
    );
    expect(screen.getByText(/#3 on the waitlist/i)).toBeInTheDocument();
  });

  it("shows a short label for other statuses (e.g. checked_in)", () => {
    render(
      <RegistrationStatusView
        registration={{ ...base, status: "checked_in" }}
        onRegister={noop}
        isRegistering={false}
        registerErrorMessage={null}
      />,
    );
    expect(screen.getByText(/checked in/i)).toBeInTheDocument();
  });

  it("shows a cancel button for an active registration when onCancel is set", async () => {
    const onCancel = vi.fn();
    render(
      <RegistrationStatusView
        registration={base}
        gymTimeZone="America/New_York"
        onRegister={noop}
        isRegistering={false}
        registerErrorMessage={null}
        onCancel={onCancel}
        isCancelling={false}
      />,
    );
    const button = screen.getByRole("button", {
      name: /cancel registration/i,
    });
    await userEvent.click(button);
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("omits the cancel button when onCancel is not provided", () => {
    render(
      <RegistrationStatusView
        registration={base}
        gymTimeZone="America/New_York"
        onRegister={noop}
        isRegistering={false}
        registerErrorMessage={null}
      />,
    );
    expect(
      screen.queryByRole("button", { name: /cancel registration/i }),
    ).not.toBeInTheDocument();
  });

  it("does not show a cancel button for an inactive (cancelled) registration", () => {
    render(
      <RegistrationStatusView
        registration={{ ...base, status: "cancelled" }}
        onRegister={noop}
        isRegistering={false}
        registerErrorMessage={null}
        onCancel={vi.fn()}
        isCancelling={false}
      />,
    );
    expect(
      screen.queryByRole("button", { name: /cancel registration/i }),
    ).not.toBeInTheDocument();
  });

  it("disables the cancel button and shows progress while cancelling", () => {
    render(
      <RegistrationStatusView
        registration={base}
        onRegister={noop}
        isRegistering={false}
        registerErrorMessage={null}
        onCancel={vi.fn()}
        isCancelling={true}
      />,
    );
    const button = screen.getByRole("button", { name: /cancelling/i });
    expect(button).toBeDisabled();
  });
});

describe("registrationErrorMessage", () => {
  it("maps a known code to a friendly message", () => {
    const err = new ApiError(409, "conflict", "already_registered");
    expect(registrationErrorMessage(err)).toMatch(/already registered/i);
  });

  it("falls back to a generic message for an unknown error", () => {
    expect(registrationErrorMessage(new Error("boom"))).toMatch(
      /could not register/i,
    );
  });
});
