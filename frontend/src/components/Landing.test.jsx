import React, { act } from "react";
import { createRoot } from "react-dom/client";
import Landing from "./Landing";
import { getCards, getCardUpdates, getResult, getSiteContent } from "../api";

jest.mock("../api", () => ({ getCards: jest.fn(), getCardUpdates: jest.fn(), getResult: jest.fn(), getSiteContent: jest.fn() }));
jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test("presents the commercial proposition with transparent trust links", async () => {
  getResult.mockResolvedValue({ scored: [] });
  getCardUpdates.mockResolvedValue({ updates: [] });
  getSiteContent.mockResolvedValue({ featured_cards: [] });
  getCards.mockResolvedValue([
    { issuer: "Bank A", verifiedOn: "2026-09-10" },
    { issuer: "Bank B", verifiedOn: "2026-10-17" },
  ]);
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<Landing onStart={jest.fn()} />));
  await act(async () => Promise.resolve());
  expect(container.textContent).toContain("find the best card for your needs");
  expect(container.textContent).toContain("Clear comparisons. Honest trade-offs. Built around you.");
  expect(container.textContent).not.toContain("Independent.");
  expect(container.textContent).not.toContain("Evidence-led");
  expect(container.textContent).not.toContain("How CardIQ makes money");
  expect(container.textContent).not.toContain("confident recommendation");
  expect(container.textContent).toContain("2 cards from 2 banks and issuers");
  expect(container.textContent).toContain("card categories");
  expect(container.textContent).toContain("What would you like to do?");
  expect(container.textContent).toContain("Compare cards");
  expect(container.textContent).toContain("Calculate my annual value");
  expect(container.textContent).toContain("Read credit card guides");
  expect(container.textContent).not.toContain("More CardIQ tools");
  expect(container.textContent).toContain("Close a card");
  expect(container.textContent).toContain("Invite-only cards");
  expect(container.textContent).toContain("Card comparisons");
  expect(container.textContent).toContain("Reviews & editorials");
  expect(container.textContent.match(/Find my best card/g)).toHaveLength(2);
  expect(container.textContent).not.toContain("Search and explore all cards");
  const closureLink = Array.from(container.querySelectorAll("a")).find((link) => link.textContent === "Close a card");
  expect(closureLink.getAttribute("href")).toBe("/help/issuers");
  const guides = Array.from(container.querySelectorAll("a")).find((link) => link.textContent.includes("credit card guides"));
  expect(guides.getAttribute("href")).toContain("/guides/");
  expect(container.querySelector("header").className).toContain("ciq-container--wide");
  expect(container.querySelector("h1").className).toContain("lg:text-6xl");
  expect(container.querySelector(".lg\\:grid-cols-3")).not.toBeNull();
  expect(Array.from(container.querySelectorAll("section")).find((section) => section.textContent.includes("Start with what you need"))?.className).toContain("mt-20");
  await act(async () => root.unmount());
});

test("refreshes a saved result label instead of showing a cached card name", async () => {
  getCardUpdates.mockResolvedValue({ updates: [] });
  getSiteContent.mockResolvedValue({ featured_cards: [] });
  getCards.mockResolvedValue([]);
  getResult.mockResolvedValue({ scored: [{ card: { name: "Current Card Name" } }] });
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<Landing onStart={jest.fn()} savedResult={{ resultId: "saved-1", cardName: "Old Card Name" }} />));
  await act(async () => Promise.resolve());
  expect(getResult).toHaveBeenCalledWith("saved-1");
  expect(container.textContent).toContain("Open saved result · Current Card Name");
  expect(container.textContent).not.toContain("Old Card Name");
  await act(async () => root.unmount());
});
