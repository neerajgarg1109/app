import React, { act } from "react";
import { createRoot } from "react-dom/client";
import PurchaseOptimizer from "./PurchaseOptimizer";
import { getCards, optimizePurchase } from "../api";

jest.mock("../api", () => ({ getCards: jest.fn(), optimizePurchase: jest.fn() }));
jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test("requires an owned card and amount before optimizing", async () => {
  getCards.mockResolvedValue([{ id: "one", name: "Card One", issuer: "Bank" }]);
  const container = document.createElement("div"); document.body.appendChild(container); const root = createRoot(container);
  await act(async () => root.render(<PurchaseOptimizer />)); await act(async () => Promise.resolve());
  await act(async () => container.querySelector("form").dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })));
  expect(container.textContent).toContain("Choose at least one card"); expect(optimizePurchase).not.toHaveBeenCalled();
  await act(async () => root.unmount()); container.remove();
});
