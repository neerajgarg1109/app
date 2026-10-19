import React, { act } from "react";
import { createRoot } from "react-dom/client";
import CustomerFooter from "./CustomerFooter";
import { getSiteContent } from "../api";

let mockPathname = "/";
jest.mock("react-router-dom", () => ({
  Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a>,
  useLocation: () => ({ pathname: mockPathname, search: "" }),
}));
jest.mock("./Logo", () => () => <div>CardIQ</div>);
jest.mock("../api", () => ({ getSiteContent: jest.fn() }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test("exposes customer discovery, comparison, support and disclosure links", async () => {
  mockPathname = "/";
  getSiteContent.mockRejectedValue(new Error("offline"));
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<CustomerFooter />));
  const links = Array.from(container.querySelectorAll("a")).map((link) => link.textContent);
  expect(links).toEqual(expect.arrayContaining(["Browse all cards", "Card comparisons", "Reviews and editorials", "How to close a card", "Annual value calculator", "How CardIQ makes money"]));
  expect(container.textContent).not.toContain("may earn a commission");
  await act(async () => root.unmount());
});

test("does not show the customer footer inside admin", async () => {
  mockPathname = "/admin";
  getSiteContent.mockRejectedValue(new Error("offline"));
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<CustomerFooter />));
  expect(container.querySelector("footer")).toBeNull();
  await act(async () => root.unmount());
});

test("does not prefix the public path twice for stored static links", async () => {
  mockPathname = "/";
  process.env.PUBLIC_URL = "/app";
  getSiteContent.mockResolvedValue({
    footer_groups: [{ title: "Research", links: [{ label: "Guides", url: "/app/guides/" }] }],
  });
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<CustomerFooter />));
  expect(container.querySelector('a[href="/app/guides/"]')).not.toBeNull();
  expect(container.querySelector('a[href="/app/app/guides/"]')).toBeNull();
  await act(async () => root.unmount());
  delete process.env.PUBLIC_URL;
});
