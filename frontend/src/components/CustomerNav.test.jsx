import React, { act } from "react";
import { createRoot } from "react-dom/client";
import CustomerNav from "./CustomerNav";

jest.mock("react-router-dom", () => ({
  Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a>,
}));
global.IS_REACT_ACT_ENVIRONMENT = true;

test("keeps high-intent customer journeys directly discoverable", async () => {
  window.location.hash = "#/";
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<CustomerNav />));
  const links = Object.fromEntries(Array.from(container.querySelectorAll("a")).map((link) => [link.textContent, link.getAttribute("href")]));
  expect(links["Home"]).toBe("/");
  expect(container.querySelector('a[href="/"]').getAttribute("aria-current")).toBe("page");
  expect(links["Browse cards"]).toBe("/cards");
  expect(links["Card comparisons"]).toBe("/cards?mode=compare");
  expect(links["Reviews & editorials"]).toContain("/guides/");
  expect(links["Close a card"]).toBe("/help/issuers");
  expect(links["Invite-only cards"]).toBe("/restricted-cards");
  expect(Array.from(container.querySelectorAll("a")).find((link) => link.textContent === "Close a card").hasAttribute("aria-current")).toBe(false);
  expect(container.querySelector("nav").getAttribute("aria-label")).toBe("Main navigation");
  expect(container.textContent).not.toContain("Explore CardIQ");
  await act(async () => root.unmount());
});

test("highlights close a card only on the issuer-help route", async () => {
  window.location.hash = "#/help/issuers";
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<CustomerNav />));
  const close = Array.from(container.querySelectorAll("a")).find((link) => link.textContent === "Close a card");
  expect(close.getAttribute("aria-current")).toBe("page");
  expect(container.querySelector('a[href="/"]').hasAttribute("aria-current")).toBe(false);
  await act(async () => root.unmount());
  window.location.hash = "#/";
});
