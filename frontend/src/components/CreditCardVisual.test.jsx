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
