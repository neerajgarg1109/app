import { trackProductEvent } from "./api";
import { productSessionId, recordProductEvent } from "./productAnalytics";

jest.mock("./api", () => ({ trackProductEvent: jest.fn() }));

describe("privacy-safe product analytics", () => {
  beforeEach(() => {
    localStorage.clear();
    trackProductEvent.mockReset();
  });

  test("reuses one anonymous session without collecting profile data", () => {
    const first = productSessionId();
    expect(first).toMatch(/^[A-Za-z0-9_-]{16,80}$/);
    expect(productSessionId()).toBe(first);
    expect(localStorage).toHaveLength(1);
  });

  test("forwards only the event, anonymous session and optional result id", async () => {
    trackProductEvent.mockResolvedValue({ status: "recorded" });
    await recordProductEvent("result_viewed", "result-123");
    expect(trackProductEvent).toHaveBeenCalledWith(
      "result_viewed",
      productSessionId(),
      "result-123",
      expect.objectContaining({ experiment_id: "landing-cta-clarity-v1", variant: expect.any(String) }),
    );
  });

  test("forwards privacy-safe content share dimensions", async () => {
    trackProductEvent.mockResolvedValue({ status: "recorded" });
    await recordProductEvent("content_shared", null, { card_id: "cashback-card", channel: "whatsapp", page_type: "card" });
    expect(trackProductEvent).toHaveBeenCalledWith("content_shared", productSessionId(), null, expect.objectContaining({
      card_id: "cashback-card", channel: "whatsapp", page_type: "card",
      experiment_id: "landing-cta-clarity-v1",
    }));
  });

  test("never blocks the journey when analytics is unavailable", async () => {
    trackProductEvent.mockRejectedValue(new Error("offline"));
    await expect(recordProductEvent("quiz_started")).resolves.toBeNull();
  });
});
