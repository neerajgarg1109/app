import React, { act } from "react";
import { createRoot } from "react-dom/client";
import IssuerHelp from "./IssuerHelp";

jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));

global.IS_REACT_ACT_ENVIRONMENT = true;

test("shows only sourced issuer support and filters it", async () => {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(<IssuerHelp />));
  expect(container.textContent).toContain("SBI Card");
  expect(container.textContent).toContain("Before closing a card");
  const input = container.querySelector('input[aria-label="Search issuers"]');
  await act(async () => {
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
    setter.call(input, "ICICI");
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
  expect(container.textContent).toContain("ICICI Bank");
  expect(container.textContent).not.toContain("SBI Card");
  await act(async () => root.unmount());
  container.remove();
});
