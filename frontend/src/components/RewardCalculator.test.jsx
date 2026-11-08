import React, { act } from "react";
import { createRoot } from "react-dom/client";
import RewardCalculator from "./RewardCalculator";
import { calculateCardRewards, getCards } from "../api";

jest.mock("../api", () => ({ getCards: jest.fn(), calculateCardRewards: jest.fn() }));
jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test("requires a selected card and positive spend", async () => {
  getCards.mockResolvedValue([{ id: "one", name: "Card One", issuer: "Bank" }]);
  const container = document.createElement("div"); document.body.appendChild(container); const root = createRoot(container);
  await act(async () => root.render(<RewardCalculator />));
  await act(async () => container.querySelector("form").dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })));
  expect(container.textContent).toContain("Select at least one card");
  await act(async () => root.unmount()); container.remove();
});

test("submits selected card and shows comparative valuations", async () => {
  getCards.mockResolvedValue([{ id: "one", name: "Card One", issuer: "Bank" }]);
  calculateCardRewards.mockResolvedValue({
    assumptions: { note: "Illustrative values" },
    results: [{ card_id: "one", card_name: "Card One", issuer: "Bank", reward_currency: "Points", reward_type: "points", points_earned: 100, effective_value_inr: 80, valuations: { transfer_partner: 80, statement_credit: 25, voucher: 40 }, rationale: "Published rate." }],
  });
  const container = document.createElement("div"); document.body.appendChild(container); const root = createRoot(container);
  await act(async () => root.render(<RewardCalculator />));
  await act(async () => { container.querySelector('input[type="checkbox"]').click(); });
  await act(async () => { const input = container.querySelector('input[aria-label="Transaction amount"]'); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(input, "1000"); input.dispatchEvent(new Event("input", { bubbles: true })); });
  await act(async () => container.querySelector("form").dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })));
  expect(calculateCardRewards).toHaveBeenCalledWith({ card_ids: ["one"], category: "dining", amount: 1000, redemption_preference: "transfer_partner" });
  expect(container.textContent).toContain("Statement credit*");
  expect(container.textContent).toContain("Card One");
  await act(async () => root.unmount()); container.remove();
});
