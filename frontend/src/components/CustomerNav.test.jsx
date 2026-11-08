import React, { act } from "react";
import { createRoot } from "react-dom/client";
import CustomerNav from "./CustomerNav";
jest.mock("react-router-dom", () => ({Link: ({to, children, ...props}) => <a href={to} {...props}>{children}</a>}));
global.IS_REACT_ACT_ENVIRONMENT = true;
test("shows distinct value and reward calculators in navigation", async () => {
 window.location.hash = "#/";
 const container = document.createElement("div"); const root = createRoot(container);
 await act(async () => root.render(<CustomerNav />));
 const links = Array.from(container.querySelectorAll("a"));
 expect(links[3].textContent).toContain("Value Calculator");
 expect(links[4].textContent).toBe("Reward & Transfer Calculator");
 expect(links.map(a => a.getAttribute("href"))).toEqual(["/", "/compare/", "/catalog/", "/calculator/", "/reward-calculator", "/lounges/", "/guides/"]);
 expect(links[0].getAttribute("aria-current")).toBe("page");
 expect(container.textContent).not.toContain("Close a card");
 expect(container.textContent).not.toContain("Invite-only");
 await act(async () => root.unmount());
});

 
test("marks the reward calculator navigation item active on its route", async () => {
 window.location.hash = "#/reward-calculator";
 const container = document.createElement("div"); const root = createRoot(container);
 await act(async () => root.render(<CustomerNav />));
 expect(container.querySelector('a[href="/reward-calculator"]').getAttribute("aria-current")).toBe("page");
 await act(async () => root.unmount());
});
