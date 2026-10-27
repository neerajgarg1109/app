import React, { act } from "react";
import { createRoot } from "react-dom/client";
import RestrictedCards from "./RestrictedCards";
import { getRestrictedCards } from "../api";

jest.mock("../api", () => ({ getRestrictedCards: jest.fn() }));
jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test("explains restricted access without presenting it as approval or an application", async () => {
  getRestrictedCards.mockResolvedValue({ cards: [{ id: "private", name: "Private Card", issuer: "Example Bank", accessType: "invite-only", accessLabel: "Invitation only", accessExplanation: "Available only after an issuer invitation.", rewardLine: "Premium rewards", annualFee: "₹10,000", sourceUrls: ["https://bank.example/private"] }] });
  const container = document.createElement("div"); const root = createRoot(container);
  await act(async () => root.render(<RestrictedCards />)); await act(async () => Promise.resolve());
  expect(container.textContent).toContain("Private Card");
  expect(container.textContent).toContain("excluded from the CardIQ quiz");
  expect(container.textContent).toContain("Access is not guaranteed");
  expect(container.textContent).not.toContain("Apply now");
  expect(container.querySelector('a[href="/cards/private"]')).not.toBeNull();
  await act(async () => root.unmount());
});


test("shows only invitation cards by default and keeps other access types behind filters", async () => {
  getRestrictedCards.mockResolvedValue({ cards: [
    { id: "invite", name: "Invitation Card", accessType: "invite-only" },
    { id: "relationship", name: "Relationship Card", accessType: "existing-relationship" },
    { id: "segment", name: "Professional Card", accessType: "segment-restricted" },
  ] });
  const container = document.createElement("div"); const root = createRoot(container);
  await act(async () => root.render(<RestrictedCards />));
  expect(container.querySelectorAll("article")).toHaveLength(1);
  expect(container.querySelector("article").textContent).toContain("Invitation Card");
  expect(container.querySelector("h1").textContent).toBe("Invite-only credit cards in India");
  const buttons = [...container.querySelectorAll("button")];
  await act(async () => buttons.find(button => button.textContent === "All restricted access").click());
  expect(container.querySelectorAll("article")).toHaveLength(3);
  expect(container.querySelector("h1").textContent).toBe("Restricted-access credit cards in India");
  await act(async () => buttons.find(button => button.textContent === "Existing relationship").click());
  expect(container.querySelectorAll("article")).toHaveLength(1);
  expect(container.querySelector("article").textContent).toContain("Relationship Card");
  await act(async () => buttons.find(button => button.textContent === "Invitation only").click());
  expect(container.querySelectorAll("article")).toHaveLength(1);
  expect(container.querySelector("article").textContent).toContain("Invitation Card");
  await act(async () => root.unmount());
});
