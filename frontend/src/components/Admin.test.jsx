import React, { act } from "react";
import { createRoot } from "react-dom/client";
import Admin from "./Admin";
import {
  getAdminCards, getAdminCardReviews, getAdminInsights, getAdminLeads,
  updateAdminCardApplyLink,
} from "../api";

jest.mock("../api", () => ({
  getAdminLeads: jest.fn(), getAdminInsights: jest.fn(), getAdminCards: jest.fn(),
  getAdminCardReviews: jest.fn(), updateAdminCardApplyLink: jest.fn(),
  createAdminCard: jest.fn(), updateAdminCard: jest.fn(), publishAdminCard: jest.fn(),
  discardAdminCardDraft: jest.fn(), getAdminCardHistory: jest.fn(), rollbackAdminCard: jest.fn(),
  archiveAdminCard: jest.fn(), previewAdminCardRecommendation: jest.fn(), exportAdminCards: jest.fn(),
  importAdminCards: jest.fn(), leadsCsvUrl: jest.fn(), sendReminders: jest.fn(),
  moderateAdminCardReview: jest.fn(), sendAdminReviewReminders: jest.fn(),
  getAdminApplyLinkHealth: jest.fn(), checkAdminApplyLinks: jest.fn(), importAdminReconciliation: jest.fn(),
}));

global.IS_REACT_ACT_ENVIRONMENT = true;

const card = {
  id: "cashback-card", name: "Everyday Cashback", issuer: "Alpha Bank", network: "Visa",
  variants: ["Visa"], official_apply_url: "https://alpha.example/card",
  custom_apply_url: "https://partner.example/apply", effective_apply_url: "https://partner.example/apply",
  partner_name: "Partner Network", campaign_id: "launch-1", tracking_id: "card-page",
  apply_link_status: "testing", expected_payout: 900, publication_status: "published",
  applyUrl: "https://alpha.example/card", sourceUrls: ["https://alpha.example/card"],
  rewardLine: "5% eligible cashback", highlights: ["Monthly cap applies."],
  annualFee: "₹999 + GST", joiningFee: "₹999 + GST", bestFor: ["cashback"],
  verifiedOn: "2026-10-17", rating: 4, active: true, applicationsOpen: true,
};

function setInput(input, value) {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  setter.call(input, value);
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

function click(container, text) {
  return Array.from(container.querySelectorAll("button")).find((button) => button.textContent.trim() === text);
}

describe("Admin partner-link workflow", () => {
  let container;
  let root;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    getAdminLeads.mockResolvedValue({ total: 0, leads: [] });
    getAdminInsights.mockResolvedValue({
      total_results: 2, emails_sent: 0, incomplete_sessions: 0, by_card: [], by_goal: [], funnel: {},
      application_performance: {
        total_clicks: 10, partner_clicks: 6, official_clicks: 4, monetised_click_rate: 60,
        expected_payout_pipeline: 5400, by_partner: [{ label: "Partner Network", count: 6, pct: 100 }],
      },
    });
    getAdminCards.mockResolvedValue({ role: "owner", cards: [card] });
    getAdminCardReviews.mockResolvedValue({ reviews: [] });
    require("../api").getAdminApplyLinkHealth.mockResolvedValue({ links: [], failed: 0 });
    updateAdminCardApplyLink.mockResolvedValue({
      custom_apply_url: "https://partner.example/live", effective_apply_url: "https://partner.example/live",
      partner_name: "Partner Network", campaign_id: "launch-2", tracking_id: "result-page",
      apply_link_status: "live", expected_payout: 1250,
    });
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(async () => {
    await act(async () => root.unmount());
    container.remove();
  });

  test("shows revenue metrics and saves complete partner attribution", async () => {
    await act(async () => root.render(<Admin />));
    const password = container.querySelector('input[type="password"]');
    await act(async () => setInput(password, "owner-token"));
    await act(async () => click(container, "Unlock dashboard").click());

    expect(container.textContent).toContain("Application revenue readiness");
    expect(container.textContent).toContain("60%");
    expect(container.textContent).toContain("₹5,400");

    await act(async () => click(container, "Cards").click());
    const byPlaceholder = (value) => container.querySelector(`[placeholder="${value}"]`);
    await act(async () => {
      setInput(container.querySelector('input[type="url"]'), "https://partner.example/live");
      setInput(byPlaceholder("Campaign ID"), "launch-2");
      setInput(byPlaceholder("Tracking ID"), "result-page");
      setInput(byPlaceholder("Expected ₹ payout"), "1250");
      const select = container.querySelector("select");
      const setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set;
      setter.call(select, "live");
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await act(async () => click(container, "Save").click());

    expect(updateAdminCardApplyLink).toHaveBeenCalledWith("owner-token", "cashback-card", {
      url: "https://partner.example/live", partner: "Partner Network", campaign: "launch-2",
      tracking: "result-page", status: "live", payout: "1250",
    });
    expect(container.textContent).toContain("Everyday Cashback apply link updated.");
  });

  test("reset removes the partner override", async () => {
    await act(async () => root.render(<Admin />));
    await act(async () => setInput(container.querySelector('input[type="password"]'), "owner-token"));
    await act(async () => click(container, "Unlock dashboard").click());
    await act(async () => click(container, "Cards").click());
    await act(async () => click(container, "Reset").click());
    expect(updateAdminCardApplyLink).toHaveBeenCalledWith("owner-token", "cashback-card", null);
  });
});
