import React, { act } from "react";
import { createRoot } from "react-dom/client";
import CreditCardVisual from "./CreditCardVisual";

global.IS_REACT_ACT_ENVIRONMENT = true;
const card = { id: "card", name: "Test Card", issuer: "Test Bank", network: "Visa", palette: ["#111", "#333"], accent: "#fff" };

test("uses a restrained default width and supports compact placements", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<CreditCardVisual card={card} />));
  expect(container.firstChild.className).toContain("max-w-[320px]");
  await act(async () => root.render(<CreditCardVisual card={card} size="sm" />));
  expect(container.firstChild.className).toContain("max-w-[220px]");
  await act(async () => root.unmount());
});

test("shows authentic artwork, handles failures, and resets for a different card", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<CreditCardVisual card={{ ...card, imageUrl: "/cards/real-card.png" }} size="thumbnail" />));
  expect(container.querySelector("img").getAttribute("src")).toBe("/cards/real-card.png");
  expect(container.querySelector("img").alt).toBe("Test Card card");
  await act(async () => container.querySelector("img").dispatchEvent(new Event("error")));
  expect(container.querySelector("img")).toBeNull();
  expect(container.textContent).toContain("Artwork unavailable");
  await act(async () => root.render(<CreditCardVisual card={{ ...card, id: "next", imageUrl: "/cards/next.png" }} />));
  expect(container.querySelector("img").getAttribute("src")).toBe("/cards/next.png");
  await act(async () => root.unmount());
});

test("finds maintained artwork for older result payloads without imageUrl", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<CreditCardVisual card={{ id: "amex-smart-earn-credit-card", name: "Amex SmartEarn" }} />));
  expect(container.querySelector("img").getAttribute("src")).toMatch(/^\/cards\/amex-smart-earn-credit-card-.*\.webp$/);
  await act(async () => root.unmount());
});
