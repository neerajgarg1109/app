import React, { act } from "react";
import { createRoot } from "react-dom/client";
import SharePanel from "./SharePanel";
import { recordProductEvent } from "../productAnalytics";

jest.mock("../productAnalytics", () => ({ recordProductEvent: jest.fn() }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test("offers social, native and copy sharing while tracking anonymous dimensions", async () => {
  const writeText = jest.fn().mockResolvedValue(undefined);
  const nativeShare = jest.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
  Object.defineProperty(navigator, "share", { configurable: true, value: nativeShare });
  const open = jest.spyOn(window, "open").mockReturnValue(null);
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<SharePanel card={{ id: "cashback-card", name: "Cashback Card", issuer: "Test Bank", rewardLine: "5% cashback" }} />));

  const button = (label) => Array.from(container.querySelectorAll("button")).find((item) => item.textContent === label);
  await act(async () => button("WhatsApp").click());
  expect(open.mock.calls[0][0]).toContain("wa.me");
  expect(recordProductEvent).toHaveBeenCalledWith("content_shared", null, { card_id: "cashback-card", channel: "whatsapp", page_type: "card" });

  await act(async () => button("Copy link").click());
  expect(writeText).toHaveBeenCalledWith("https://neerajgarg1109.github.io/app/cards/cashback-card/");
  expect(container.textContent).toContain("Copied");

  await act(async () => button("More sharing options").click());
  expect(nativeShare).toHaveBeenCalledWith(expect.objectContaining({ title: "Cashback Card | CardIQ" }));

  await act(async () => root.unmount());
  open.mockRestore();
});
