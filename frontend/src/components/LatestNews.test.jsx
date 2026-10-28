import React, { act } from "react";
import { createRoot } from "react-dom/client";
import LatestNews from "./LatestNews";
import CARD_NEWS from "../data/cardNews.json";

global.IS_REACT_ACT_ENVIRONMENT = true;

test("shows the sourced ICICI announcement without presenting it as an open application or confirmed future launch", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<LatestNews items={CARD_NEWS} />));
  expect(container.textContent).toContain("Latest news");
  expect(container.textContent).toContain("1838 Reserve");
  expect(container.textContent).toContain("Invitation only");
  expect(container.textContent).toContain("Currently listed by ICICI Bank; invitation required");
  expect(container.textContent).not.toContain("Apply now");
  expect(container.textContent).not.toContain("Coming soon");
  const source = container.querySelector("a");
  expect(source.getAttribute("href")).toBe(CARD_NEWS[0].sourceUrl);
  expect(source.getAttribute("rel")).toContain("noopener");
  expect(container.querySelector("time").getAttribute("datetime")).toBe(CARD_NEWS[0].verifiedOn);
  await act(async () => root.unmount());
});

test("removes launched and withdrawn announcements from upcoming news", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<LatestNews items={[
    { ...CARD_NEWS[0], id: "launched", status: "launched" },
    { ...CARD_NEWS[0], id: "withdrawn", active: false },
  ]} />));
  expect(container.textContent).toBe("");
  await act(async () => root.unmount());
});
