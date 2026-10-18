import React, { act } from "react";
import { createRoot } from "react-dom/client";
import CardAlerts from "./CardAlerts";
import { getCards, subscribeCardAlerts } from "../api";

jest.mock("../api", () => ({ getCards: jest.fn(), subscribeCardAlerts: jest.fn() }));
jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test("requires explicit alert consent and submits a scoped preference", async () => {
  getCards.mockResolvedValue([{ id: "card-one", name: "Card One", issuer: "Bank One" }]);
  subscribeCardAlerts.mockResolvedValue({ status: "subscribed" });
  const container = document.createElement("div"); document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(<CardAlerts />)); await act(async () => Promise.resolve());
  const form = container.querySelector("form");
  await act(async () => form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })));
  expect(container.textContent).toContain("Enter a valid email address");
  expect(subscribeCardAlerts).not.toHaveBeenCalled();
  await act(async () => root.unmount()); container.remove();
});
