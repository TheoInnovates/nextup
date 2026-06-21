import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RosterView } from "@/components/RosterView";
import { type RosterEntry, type RosterResponse } from "@/lib/roster";

function entry(overrides: Partial<RosterEntry> = {}): RosterEntry {
  return {
    registration_id: "reg-1",
    player_user_id: "player-1",
    player_display_name: "Alex Hooper",
    player_email: "alex@example.com",
    status: "confirmed",
    queue_position: null,
    assigned_slot_number: 4,
    // 22:00 UTC -> 6:00 PM in America/New_York (EDT, -4 in June).
    assigned_arrival_time: "2026-06-23T21:45:00Z",
    estimated_play_time: "2026-06-23T22:00:00Z",
    checked_in_at: null,
    ...overrides,
  };
}

const noop = () => {};

function roster(overrides: Partial<RosterResponse> = {}): RosterResponse {
  return {
    run_id: "run-1",
    confirmed: [entry()],
    waitlist: [
      entry({
        registration_id: "reg-2",
        player_display_name: "Bo Waitman",
        status: "waitlisted",
        queue_position: 1,
        assigned_slot_number: null,
        assigned_arrival_time: null,
        estimated_play_time: null,
      }),
    ],
    no_show: [
      entry({
        registration_id: "reg-3",
        player_display_name: "Casey Gone",
        status: "no_show",
      }),
    ],
    ...overrides,
  };
}

describe("RosterView", () => {
  it("renders confirmed, waitlist, and no-show entries", () => {
    render(
      <RosterView
        roster={roster()}
        gymTimeZone="America/New_York"
        onCheckIn={noop}
        onNoShow={noop}
      />,
    );
    expect(screen.getByText("Alex Hooper")).toBeInTheDocument();
    expect(screen.getByText("Bo Waitman")).toBeInTheDocument();
    expect(screen.getByText("Casey Gone")).toBeInTheDocument();
    // Slot and the play time formatted in the gym zone.
    expect(screen.getByText(/Slot #4/)).toBeInTheDocument();
    // U+202F narrow no-break space before AM/PM in Node 22 ICU — match loosely.
    expect(screen.getByText(/6:00\s*PM/)).toBeInTheDocument();
    // Waitlist position.
    expect(screen.getByText(/#1/)).toBeInTheDocument();
  });

  it("calls onCheckIn with the registration id when Check in is clicked", async () => {
    const onCheckIn = vi.fn();
    render(
      <RosterView
        roster={roster()}
        gymTimeZone="America/New_York"
        onCheckIn={onCheckIn}
        onNoShow={noop}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /check in/i }));
    expect(onCheckIn).toHaveBeenCalledOnce();
    expect(onCheckIn).toHaveBeenCalledWith("reg-1");
  });

  it("calls onNoShow with the registration id when No-show is clicked", async () => {
    const onNoShow = vi.fn();
    render(
      <RosterView
        roster={roster()}
        gymTimeZone="America/New_York"
        onCheckIn={noop}
        onNoShow={onNoShow}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /no-show/i }));
    expect(onNoShow).toHaveBeenCalledOnce();
    expect(onNoShow).toHaveBeenCalledWith("reg-1");
  });

  it("shows a checked-in state instead of attendance buttons", () => {
    render(
      <RosterView
        roster={roster({
          confirmed: [
            entry({ status: "checked_in", checked_in_at: "2026-06-23T21:50:00Z" }),
          ],
        })}
        gymTimeZone="America/New_York"
        onCheckIn={noop}
        onNoShow={noop}
      />,
    );
    expect(screen.getByText(/checked in/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /check in/i }),
    ).not.toBeInTheDocument();
  });

  it("renders empty-state copy for each section when there are no entries", () => {
    render(
      <RosterView
        roster={{ run_id: "run-1", confirmed: [], waitlist: [], no_show: [] }}
        gymTimeZone="America/New_York"
        onCheckIn={noop}
        onNoShow={noop}
      />,
    );
    expect(screen.getByText(/no confirmed players yet/i)).toBeInTheDocument();
    expect(screen.getByText(/no one is waitlisted/i)).toBeInTheDocument();
    expect(screen.getByText(/no no-shows/i)).toBeInTheDocument();
  });
});
