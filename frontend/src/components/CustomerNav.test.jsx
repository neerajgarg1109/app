import React, { act } from "react";
import { createRoot } from "react-dom/client";
import CustomerNav from "./CustomerNav";

jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test("keeps high-intent customer journeys directly discoverable", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<CustomerNav />));
  const links = Object.fromEntries(Array.from(container.querySelectorAll("a")).map((link) => [link.textContent, link.getAttribute("href")]));
  expect(links["Browse cards"]).toBe("/cards");
  expect(links["Card comparisons"]).toBe("/cards?mode=compare");
  expect(links["Reviews & editorials"]).toContain("/guides/");
  expect(links["Close a card"]).toBe("/help/issuers");
  expect(links["Invite-only cards"]).toBe("/restricted-cards");
  expect(container.querySelector("nav").getAttribute("aria-label")).toBe("Explore CardIQ");
  await act(async () => root.unmount());
});
