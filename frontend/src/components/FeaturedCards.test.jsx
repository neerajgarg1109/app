import React, { act } from "react";
import { createRoot } from "react-dom/client";
import FeaturedCards from "./FeaturedCards";
import { trackApplyClick } from "../api";

jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));
jest.mock("./CreditCardVisual", () => ({ card }) => <div>{card.name} image</div>);
jest.mock("../api", () => ({ trackApplyClick: jest.fn(() => Promise.resolve()) }));
jest.mock("../productAnalytics", () => ({ recordProductEvent: jest.fn() }));
global.IS_REACT_ACT_ENVIRONMENT = true;

const cards = [
  { id: "partner", name: "Partner Card", issuer: "Bank A", applicationLinkType: "partner", rewardLine: "Partner rewards", applyUrl: "https://bank.example/partner" },
  { id: "launch", name: "Launch Card", issuer: "Bank B", applicationLinkType: "official", rewardLine: "Launch rewards", applyUrl: "https://bank.example/launch" },
];

test("labels paid placement and new launches without changing rankings", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<FeaturedCards cards={cards} updates={[{ card_id: "launch", change_type: "launch", summary: "Recently launched." }]} />));
  expect(container.textContent).toContain("Partner feature");
  expect(container.textContent).toContain("Offers from CardIQ partners");
  expect(container.textContent).toContain("New cards worth knowing about");
  expect(container.textContent).toContain("Promoted placement");
  expect(container.textContent).toContain("New launch");
  expect(container.textContent).toContain("Promotion never changes match scores");
  expect(Array.from(container.querySelectorAll("a")).map((link) => link.getAttribute("href"))).toEqual(expect.arrayContaining(["/cards/partner", "/cards/launch", "/updates"]));
  const launchApply = Array.from(container.querySelectorAll("a")).find((link) => link.getAttribute("href") === "https://bank.example/launch");
  expect(launchApply.textContent).toContain("Apply now");
  await act(async () => launchApply.click());
  expect(trackApplyClick).toHaveBeenCalledWith("launch", null);
  await act(async () => root.unmount());
});

test("stays hidden when admin has configured neither a partner feature nor a launch", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<FeaturedCards cards={[{ ...cards[0], applicationLinkType: "official" }]} updates={[]} />));
  expect(container.textContent).toBe("");
  await act(async () => root.unmount());
});

test("shows a catalogue-configured launch without relying on a hardcoded card id", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  const configured = { ...cards[1], homepagePlacement: { active: true, type: "launch", label: "Just launched", priority: 50, summary: "Configured summary." } };
  await act(async () => root.render(<FeaturedCards cards={[configured]} updates={[]} />));
  expect(container.textContent).toContain("Just launched");
  expect(container.textContent).toContain("Configured summary.");
  expect(container.textContent).not.toContain("Promoted placement");
  await act(async () => root.unmount());
});
