import React, { act } from "react";
import { createRoot } from "react-dom/client";
import Landing from "./Landing";
import { getCards } from "../api";

jest.mock("../api", () => ({ getCards: jest.fn() }));
jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test("presents the commercial proposition with transparent trust links", async () => {
  getCards.mockResolvedValue([{ issuer: "Bank A" }, { issuer: "Bank B" }]);
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<Landing onStart={jest.fn()} />));
  await act(async () => Promise.resolve());
  expect(container.textContent).toContain("explains its strongest recommendation");
  expect(container.textContent).toContain("not a sponsored leaderboard");
  expect(container.textContent).toContain("methodology and revenue disclosure");
  expect(container.textContent).not.toContain("confident recommendation");
  const methodology = Array.from(container.querySelectorAll("a")).find((link) => link.textContent.includes("methodology"));
  expect(methodology.getAttribute("href")).toContain("/methodology/");
  await act(async () => root.unmount());
});
