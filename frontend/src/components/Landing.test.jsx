import React, { act } from "react";
import { createRoot } from "react-dom/client";
import Landing from "./Landing";
import { getCards, getResult } from "../api";

jest.mock("../api", () => ({ getCards: jest.fn(), getResult: jest.fn() }));
jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test("presents the commercial proposition with transparent trust links", async () => {
  getResult.mockResolvedValue({ scored: [] });
  getCards.mockResolvedValue([
    { issuer: "Bank A", verifiedOn: "2026-09-10" },
    { issuer: "Bank B", verifiedOn: "2026-10-17" },
  ]);
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<Landing onStart={jest.fn()} />));
  await act(async () => Promise.resolve());
  expect(container.textContent).toContain("explains its strongest recommendation");
  expect(container.textContent).toContain("not a sponsored leaderboard");
  expect(container.textContent).toContain("methodology and revenue disclosure");
  expect(container.textContent).not.toContain("confident recommendation");
  expect(container.textContent).toContain("2 cards across 2 issuers");
  expect(container.textContent).toContain("Oct 2026");
  expect(container.textContent).toContain("More than a card quiz");
  expect(container.textContent).toContain("Compare with my card");
  const methodology = Array.from(container.querySelectorAll("a")).find((link) => link.textContent.includes("methodology"));
  expect(methodology.getAttribute("href")).toContain("/methodology/");
  await act(async () => root.unmount());
});

test("refreshes a saved result label instead of showing a cached card name", async () => {
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
