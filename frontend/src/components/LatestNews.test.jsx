import React, { act } from "react";
import { createRoot } from "react-dom/client";
import LatestNews from "./LatestNews";
import CARD_NEWS from "../data/cardNews.json";

global.IS_REACT_ACT_ENVIRONMENT = true;

test("shows only the newest sourced update with an archive link", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<LatestNews items={CARD_NEWS} />));
  expect(container.textContent).toContain("News & rule updates");
  expect(container.textContent).toContain("HDFC BizBlack revises tax rewards and 5X spend rules");
  expect(container.textContent).not.toContain("ICICI raises most card replacement fees from 11 Dec");
  expect(container.textContent).not.toContain("SBI Card adds fees above transport and fuel thresholds");
  expect(container.textContent).not.toContain("Tata Neu HDFC cardholders must claim spend-earned NeuCoins");
  expect(container.textContent).not.toContain("ICICI shares details of 1838 Reserve");
  expect(CARD_NEWS.some((item) => item.id === "icici-card-replacement-fee-dec-2026")).toBe(true);
  expect(container.querySelectorAll(".ciq-news-article")).toHaveLength(1);
  expect(container.querySelector('a[href="/guides/news/"]').textContent).toContain("All updates");
  expect(container.textContent).not.toContain("Currently listed by ICICI Bank; invitation required");
  expect(container.textContent).not.toContain("Apply now");
  expect(container.textContent).not.toContain("Coming soon");
  expect(container.textContent).toContain("hi@findmybest.cards");
  const source = container.querySelector(".ciq-news-article h3 a");
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
