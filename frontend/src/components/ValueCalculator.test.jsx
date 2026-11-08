import React, { act } from "react";
import { createRoot } from "react-dom/client";
import ValueCalculator from "./ValueCalculator";
import { calculateCardValue } from "../api";

jest.mock("../api", () => ({ calculateCardValue: jest.fn(), trackApplyClick: jest.fn() }));
jest.mock("../productAnalytics", () => ({ recordProductEvent: jest.fn() }));
let mockSearch = "";
jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a>, useLocation: () => ({ search: mockSearch }) }));
global.IS_REACT_ACT_ENVIRONMENT = true;

function input(container, label, value) {
  const field = container.querySelector(`[aria-label="${label}"]`);
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  setter.call(field, value);
  field.dispatchEvent(new Event("input", { bubbles: true }));
}

test("calculates a spend scenario without collecting contact details", async () => {
  mockSearch = "";
  calculateCardValue.mockResolvedValue({
    monthlySpend: 40000, annualSpend: 480000,
    results: [{
      card: { id: "cashback", name: "Cashback Card", issuer: "Test Bank", rewardLine: "5% eligible online cashback", applyUrl: "https://bank.example/apply", joiningFeeAmount: 999 },
      valueEstimate: { netLow: 5000, netHigh: 8000, grossLow: 6000, grossHigh: 9000, effectiveAnnualFee: 1000, feeWaived: false, firstYearBenefitsValue: 500, loungeValue: 700, economicsCoverage: 60, economicsQuality: "medium" },
    }],
  });
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(<ValueCalculator />));
  await act(async () => input(container, "Online shopping", "40000"));
  const submit = Array.from(container.querySelectorAll("button")).find((button) => button.textContent.includes("Compare annual value"));
  await act(async () => submit.click());
  expect(calculateCardValue).toHaveBeenCalledWith(expect.objectContaining({ online: 40000, dining: 0 }));
  expect(container.textContent).toContain("Cashback Card");
  expect(container.textContent).toContain("₹5,000–₹8,000");
  expect(container.textContent).toContain("First-year joining fee");
  expect(container.textContent).toContain("₹999");
  expect(container.textContent).toContain("Explicit benefits counted");
  expect(container.textContent).toContain("₹1,200");
  expect(container.textContent).toContain("Joining fees, GST on fees and interest");
  const applyLink = container.querySelector('a[href="/go/cashback/?subid=calculator_result_row&source=calculator"]');
  expect(applyLink.textContent).toBe("Apply Now →");
  expect(applyLink.getAttribute("rel")).toBe("sponsored nofollow noopener");
  expect(applyLink.getAttribute("target")).toBe("_blank");
  expect(container.querySelector('input[type="email"]')).toBeNull();
  expect(container.querySelector('input[type="tel"]')).toBeNull();
  await act(async () => root.unmount());
  container.remove();
});

test("budget presets fill their spend buckets and calculate immediately", async () => {
  mockSearch = "";
  calculateCardValue.mockResolvedValue({ monthlySpend: 25000, annualSpend: 300000, results: [] });
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<ValueCalculator />));

  await act(async () => container.querySelector('button[aria-pressed="false"]').click());
  expect(calculateCardValue).toHaveBeenLastCalledWith(expect.objectContaining({ online: 10000, dining: 5000, utilities: 5000, other: 5000 }));
  expect(container.querySelector('button[aria-pressed="true"]').textContent).toContain("Lite Spender");
  expect(container.textContent).toContain("₹25,000 a month");

  const balanced = Array.from(container.querySelectorAll("button")).find((button) => button.textContent.includes("Balanced Optimizer"));
  await act(async () => balanced.click());
  expect(calculateCardValue).toHaveBeenLastCalledWith(expect.objectContaining({ online: 25000, dining: 10000, travel: 5000, fuel: 5000, utilities: 5000, other: 10000 }));

  const hni = Array.from(container.querySelectorAll("button")).find((button) => button.textContent.includes("HNI / Travel Spender"));
  await act(async () => hni.click());
  expect(calculateCardValue).toHaveBeenLastCalledWith(expect.objectContaining({ online: 50000, travel: 40000, dining: 25000, utilities: 15000, other: 20000 }));
  await act(async () => root.unmount());
  container.remove();
});

test("removes duplicate navigation and page introduction when embedded", async () => {
  mockSearch = "?embedded=1";
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<ValueCalculator />));
  expect(container.querySelector("header")).toBeNull();
  expect(container.querySelector("h1")).toBeNull();
  expect(container.querySelector(".pt-4.text-center")).toBeNull();
  expect(container.firstChild.className).toContain("pb-4");
  expect(container.firstChild.className).not.toContain("min-h-screen");
  await act(async () => root.unmount());
});
