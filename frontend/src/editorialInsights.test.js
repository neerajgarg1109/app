import { editorialInsights } from "./editorialInsights";

test("creates card-specific guidance for a fee-bearing cashback card", () => {
  const insight = editorialInsights({
    name: "Cash Card", bestFor: ["cashback", "online"], annualFeeAmount: 999,
    annualFee: "₹999 + GST (waived on ₹2 lakh eligible annual spend)", creditReq: "good",
    highlights: ["Cashback is capped at ₹1,000 per month."],
  });
  expect(insight.verdict).toContain("cashback and online purchases");
  expect(insight.goodFit.join(" ")).toContain("fee-waiver condition");
  expect(insight.thinkTwice.join(" ")).toContain("capped");
  expect(JSON.stringify(insight)).not.toMatch(/likely to meet|approval odds|guaranteed/i);
});

test("never turns an internal credit-profile hint into underwriting advice", () => {
  const insight = editorialInsights({ name: "Prime Card", bestFor: ["travel"], annualFeeAmount: 2999, creditReq: "excellent" });
  expect(insight.goodFit.join(" ")).not.toMatch(/credit|eligible|approval|likely/i);
});

test("explains the distinct economics of free and secured cards", () => {
  const free = editorialInsights({ name: "Free Card", bestFor: ["rewards"], annualFeeAmount: 0 });
  const secured = editorialInsights({ name: "FD Card", bestFor: ["secured"], annualFeeAmount: 0, secured: true });
  expect(free.verdict).toContain("no-annual-fee structure");
  expect(secured.verdict).toContain("building credit");
});

test("prefers the maintained editorial layer over generated fallback copy", () => {
  const editorial = {
    summary: "A researched summary.", idealFor: ["Frequent travellers."], strengths: ["Useful lounge access."],
    tradeoffs: ["A quarterly cap applies."], verdict: "Worth comparing for regular travel.",
    alternatives: [{ id: "other-card", name: "Other Card", reason: "Lower fee." }],
  };
  expect(editorialInsights({ name: "Card", editorial })).toMatchObject({ ...editorial, stored: true });
});
