import React, { act } from "react";
import { createRoot } from "react-dom/client";
import ValueCalculator from "./ValueCalculator";
import { calculateCardValue } from "../api";

jest.mock("../api", () => ({ calculateCardValue: jest.fn(), trackApplyClick: jest.fn() }));
jest.mock("../productAnalytics", () => ({ recordProductEvent: jest.fn() }));
jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));
global.IS_REACT_ACT_ENVIRONMENT = true;

function input(container, label, value) {
  const field = container.querySelector(`[aria-label="${label}"]`);
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  setter.call(field, value);
  field.dispatchEvent(new Event("input", { bubbles: true }));
}

test("calculates a spend scenario without collecting contact details", async () => {
  calculateCardValue.mockResolvedValue({
    monthlySpend: 40000, annualSpend: 480000,
    results: [{
      card: { id: "cashback", name: "Cashback Card", issuer: "Test Bank", rewardLine: "5% eligible online cashback", applyUrl: "https://bank.example/apply" },
      valueEstimate: { netLow: 5000, netHigh: 8000, grossLow: 6000, grossHigh: 9000, effectiveAnnualFee: 1000, feeWaived: false },
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
  expect(container.querySelector('input[type="email"]')).toBeNull();
  expect(container.querySelector('input[type="tel"]')).toBeNull();
  await act(async () => root.unmount());
  container.remove();
});
