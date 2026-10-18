import React, { act } from "react";
import { createRoot } from "react-dom/client";
import CardUpdates from "./CardUpdates";
import { getCardUpdates } from "../api";

jest.mock("../api", () => ({ getCardUpdates: jest.fn() }));
jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test("shows sourced changes separately from verification dates", async () => {
  getCardUpdates.mockResolvedValue({ updates: [{ campaign_id: "one", change_type: "fee-change", effective_date: "2026-11-01", title: "Fee updated", card_name: "Card One", issuer: "Bank", summary: "The annual fee has changed.", card_id: "one", source_url: "https://bank.example/terms" }] });
  const container = document.createElement("div"); document.body.appendChild(container); const root = createRoot(container);
  await act(async () => root.render(<CardUpdates />)); await act(async () => Promise.resolve());
  expect(container.textContent).toContain("Fee change"); expect(container.textContent).toContain("Effective 1 Nov 2026");
  expect(container.textContent).toContain("Every update links to an official source");
  await act(async () => root.unmount()); container.remove();
});
