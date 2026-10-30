import React, { act } from "react";
import { createRoot } from "react-dom/client";
import CustomerNav from "./CustomerNav";
jest.mock("react-router-dom", () => ({Link: ({to, children, ...props}) => <a href={to} {...props}>{children}</a>}));
global.IS_REACT_ACT_ENVIRONMENT = true;
test("shows six crawlable navigation routes and keeps secondary links in the footer", async () => {
 window.location.hash = "#/";
 const container = document.createElement("div"); const root = createRoot(container);
 await act(async () => root.render(<CustomerNav />));
 const links = Array.from(container.querySelectorAll("a"));
 expect(links.map(a => a.getAttribute("href"))).toEqual(["/", "/compare/", "/catalog/", "/calculator/", "/lounges/", "/guides/"]);
 expect(links[0].getAttribute("aria-current")).toBe("page");
 expect(container.textContent).not.toContain("Close a card");
 expect(container.textContent).not.toContain("Invite-only");
 await act(async () => root.unmount());
});
