import React, { act } from "react";
import { createRoot } from "react-dom/client";
import CardDetails from "./CardDetails";

jest.mock("./CreditCardVisual", () => () => <div>Card artwork</div>);
jest.mock("./SharePanel", () => () => <div>Share this card</div>);
global.IS_REACT_ACT_ENVIRONMENT = true;

const card = {
  id: "test-card", name: "Test Card", issuer: "Test Bank", network: "Visa", palette: ["#111", "#222"], accent: "#fff",
  annualFee: "₹999 + GST", joiningFee: "₹999 + GST", rewardLine: "5% cashback on eligible online spends",
  bestFor: ["cashback", "online"], creditReq: "good", applyUrl: "https://bank.example/card", active: true, applicationsOpen: true,
  highlights: ["Cashback is capped each month.", "Fee waiver applies on eligible annual spend."], verifiedOn: "2026-10-18",
  sourceUrls: ["https://bank.example/card"], editorial: { summary: "Useful for regular online spending.", idealFor: ["Online shoppers"], strengths: ["Simple cashback"], tradeoffs: ["Monthly cap"], verdict: "Consider it if the cap fits your spending.", alternatives: [] },
};

test("puts decision-critical facts first and collapses deeper detail", async () => {
  const container = document.createElement("div");
  const root = createRoot(container);
  await act(async () => root.render(<CardDetails card={card} onApply={jest.fn()} />));
  const text = container.textContent;
  expect(text.indexOf("At a glance")).toBeLessThan(text.indexOf("Is this card right for you?"));
  expect(text.indexOf("Is this card right for you?")).toBeLessThan(text.indexOf("Check eligibility on Test Bank"));
  expect(container.querySelectorAll("details")).toHaveLength(3);
  expect(text).toContain("Main catch");
  expect(text).toContain("Checked against issuer information");
  await act(async () => root.unmount());
});
