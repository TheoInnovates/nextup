import { describe, expect, it } from "vitest";

import {
  notificationPageSchema,
  notificationSchema,
} from "@/lib/notifications";

const unread = {
  id: "11111111-1111-1111-1111-111111111111",
  type: "waitlist_promoted",
  title: "A spot opened up",
  message: "You've been promoted from the waitlist.",
  related_run_id: "22222222-2222-2222-2222-222222222222",
  is_read: false,
  created_at: "2026-06-20T12:30:00Z",
  read_at: null,
};

const read = {
  ...unread,
  id: "33333333-3333-3333-3333-333333333333",
  type: "registration_confirmed",
  related_run_id: null,
  is_read: true,
  read_at: "2026-06-20T13:00:00Z",
};

describe("notificationSchema", () => {
  it("parses a valid unread notification", () => {
    const parsed = notificationSchema.parse(unread);
    expect(parsed.type).toBe("waitlist_promoted");
    expect(parsed.is_read).toBe(false);
    expect(parsed.read_at).toBeNull();
  });

  it("parses a read notification with a null related run", () => {
    const parsed = notificationSchema.parse(read);
    expect(parsed.is_read).toBe(true);
    expect(parsed.related_run_id).toBeNull();
    expect(parsed.read_at).toBe("2026-06-20T13:00:00Z");
  });

  it("rejects an unknown type", () => {
    expect(
      notificationSchema.safeParse({ ...unread, type: "friend_request" })
        .success,
    ).toBe(false);
  });

  it("rejects a missing required field", () => {
    const { title: _omitted, ...withoutTitle } = unread;
    void _omitted;
    expect(notificationSchema.safeParse(withoutTitle).success).toBe(false);
  });
});

describe("notificationPageSchema", () => {
  it("parses a paginated envelope", () => {
    const page = { items: [unread, read], total: 2, limit: 20, offset: 0 };
    expect(notificationPageSchema.parse(page).items).toHaveLength(2);
  });

  it("parses an empty envelope", () => {
    const page = { items: [], total: 0, limit: 20, offset: 0 };
    expect(notificationPageSchema.parse(page).items).toHaveLength(0);
  });
});
