import React, { act } from "react";
import { createRoot } from "react-dom/client";
import Result from "./Result";
import {
  attachResultLead, emailResult, getCommunityRating, submitExperienceFeedback, trackApplyClick,
  trackProductEvent,
} from "../api";

jest.mock("../api", () => ({
  attachResultLead: jest.fn(), emailResult: jest.fn(), trackApplyClick: jest.fn(),
  reportCardInformation: jest.fn(), scheduleReviewFollowup: jest.fn(),
  getCommunityRating: jest.fn(), submitExperienceFeedback: jest.fn(),
  trackProductEvent: jest.fn(),
}));

global.IS_REACT_ACT_ENVIRONMENT = true;

const card = {
  id: "test-card", name: "Test Cashback Card", issuer: "Test Bank", tagline: "Simple value",
  palette: ["#123456", "#345678"], accent: "#ffffff", network: "Visa", rating: 4,
  ratingBasis: "Editorial rating", annualFee: "No annual fee", joiningFee: "No joining fee",
  annualFeeAmount: 0, joiningFeeAmount: 0, rewardLine: "5% eligible cashback",
  highlights: ["Cashback capped at ₹1,000 per month.", "No annual fee."],
  applyUrl: "https://bank.example.com/apply", officialApplyUrl: "https://bank.example.com/card",
  verifiedOn: "2026-10-11", termsNote: "Issuer conditions apply.", active: true, applicationsOpen: true,
};

const scored = [{
  card, confidence: 88, reasons: ["Gives you simple cashback"],
  valueEstimate: {
    annualSpendAssumption: 240000, grossLow: 3000, grossHigh: 5000, netLow: 3000, netHigh: 5000,
    annualFee: 0, effectiveAnnualFee: 0, feeWaived: false, firstYearBenefitsValue: 0,
    loungeValue: 0, availableLoungeValue: 0, headlinePotential: 5000, isPersonalized: false,
    methodology: "Test methodology.",
  },
}];

const alternateCard = {
  ...card, id: "alternate-card", name: "Test Travel Card", issuer: "Another Bank",
  rewardLine: "Travel rewards on eligible spend", highlights: ["Four lounge visits each year.", "Low foreign currency markup."],
};

function button(container, name) {
  return Array.from(container.querySelectorAll("button")).find((item) => item.textContent.trim() === name);
}

function setInput(input, value) {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  setter.call(input, value);
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

describe("Result customer flows", () => {
  let container;
  let root;

  beforeEach(async () => {
    jest.useFakeTimers();
    jest.clearAllMocks();
    sessionStorage.clear();
    getCommunityRating.mockResolvedValue({ published: false, count: 0, minimum: 20 });
    attachResultLead.mockResolvedValue({ status: "saved" });
    emailResult.mockResolvedValue({ status: "success", sent_to: "person@example.com" });
    submitExperienceFeedback.mockResolvedValue({ status: "received" });
    trackApplyClick.mockResolvedValue({ status: "recorded" });
    trackProductEvent.mockResolvedValue({ status: "recorded" });
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    await act(async () => root.render(<Result scored={scored} resultId="result-1" answers={{}} onRestart={jest.fn()} />));
  });

  afterEach(async () => {
    await act(async () => root.unmount());
    container.remove();
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  test("keeps the result uninterrupted and offers optional contact capture", async () => {
    await act(async () => jest.advanceTimersByTime(1201));
    expect(container.textContent).not.toContain("Keep your match handy");
    await act(async () => button(container, "Email").click());
    expect(container.textContent).toContain("Keep your match handy");
    await act(async () => button(container, "See my result without sharing details").click());
    expect(container.textContent).not.toContain("Keep your match handy");
    expect(sessionStorage.getItem("ciq_contact_prompt_result-1")).toBe("skipped");
  });

  test("blocks invalid contacts and submits a valid consented lead", async () => {
    await act(async () => button(container, "Email").click());
    await act(async () => button(container, "Save and email my result").click());
    expect(container.textContent).toContain("Enter your full name.");
    expect(container.textContent).toContain("Enter a valid 10-digit Indian mobile number.");
    expect(container.textContent).toContain("Enter a valid email address.");
    expect(attachResultLead).not.toHaveBeenCalled();

    const inputs = container.querySelectorAll("input");
    await act(async () => {
      setInput(inputs[0], "Neeraj Garg");
      setInput(inputs[1], "9876543210");
      setInput(inputs[2], "person@example.com");
      inputs[3].click();
    });
    await act(async () => button(container, "Save and email my result").click());
    expect(attachResultLead).toHaveBeenCalledWith("result-1", {
      name: "Neeraj Garg", email: "person@example.com", phone: "9876543210", contact_consent: true,
    });
    expect(emailResult).toHaveBeenCalledWith("result-1");
    expect(sessionStorage.getItem("ciq_contact_prompt_result-1")).toBe("submitted");
  });

  test("submits anonymous CardIQ experience feedback", async () => {
    await act(async () => button(container, "See my result without sharing details")?.click());
    const rating = container.querySelector('button[aria-label="4 out of 5"]');
    await act(async () => rating.click());
    const feedback = container.querySelector('textarea[placeholder*="What worked well"]');
    const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
    await act(async () => {
      setter.call(feedback, "Clear and useful recommendation.");
      feedback.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await act(async () => button(container, "Share feedback").click());
    expect(submitExperienceFeedback).toHaveBeenCalledWith(4, "Clear and useful recommendation.", "result-1", "test-card");
    expect(container.textContent).toContain("Thanks for helping us improve CardIQ.");
  });

  test("records an anonymous application handoff and opens the issuer safely", async () => {
    const target = { location: "", opener: "unsafe", close: jest.fn() };
    const open = jest.spyOn(window, "open").mockReturnValue(target);
    await act(async () => button(container, "Apply on Test Bank").click());
    expect(container.textContent).toContain("Continue to Test Bank");
    await act(async () => button(container, "Continue without a reminder").click());
    expect(trackApplyClick).toHaveBeenCalledWith("test-card", "result-1");
    expect(target.opener).toBeNull();
    expect(target.location).toBe("https://bank.example.com/apply");
    open.mockRestore();
  });

  test("discloses monetised application links without implying paid ranking", async () => {
    await act(async () => root.render(<Result scored={[{
      ...scored[0], card: { ...card, applicationLinkType: "partner", affiliateDisclosureRequired: true },
    }]} resultId="result-1" answers={{}} onRestart={jest.fn()} />));
    expect(container.textContent).toContain("CardIQ may earn a commission. Rankings are unaffected.");
  });

  test("shows every verified top-card detail and opens complete alternate features", async () => {
    await act(async () => root.render(<Result scored={[...scored, { card: alternateCard, confidence: 81, reasons: ["Travel fit"] }]} resultId="result-1" answers={{}} onRestart={jest.fn()} />));
    expect(container.textContent).toContain("All verified benefits and conditions");
    expect(container.textContent).toContain("5% eligible cashback");
    expect(container.textContent).toContain("Cashback capped at ₹1,000 per month.");
    await act(async () => container.querySelector('button[aria-label="View full details for Test Travel Card"]').click());
    expect(container.textContent).toContain("Complete features");
    expect(container.textContent).toContain("Four lounge visits each year.");
    expect(container.textContent).toContain("Low foreign currency markup.");
    expect(container.textContent).not.toContain("cardIQ rating");
  });
});
