import { catalogQualityIssues } from "./catalogQuality";

test.each(["No fee for the first four years", "₹0", "Rs. 0"])("does not mistake %s for a positive fee", (fee) => {
  const issues = catalogQualityIssues([{ annualFee: fee, annualFeeAmount: 0, joiningFee: fee, joiningFeeAmount: 0 }]);
  expect(issues.map((item) => item.issue).filter((issue) => issue.includes("fee text and amount conflict"))).toEqual([]);
});

test.each(["Rs. 500", "Rs 1,000", "₹0 initially; ₹500 later"])("preserves real fee conflicts for %s", (fee) => {
  const issues = catalogQualityIssues([{ annualFee: fee, annualFeeAmount: 0, joiningFee: fee, joiningFeeAmount: 0 }]);
  expect(issues.map((item) => item.issue)).toEqual(expect.arrayContaining(["Annual fee text and amount conflict", "Joining fee text and amount conflict"]));
});

test("detects contradictory fees, duplicate facts and unsafe sources", () => {
  const [card] = [{
    id: "broken", name: "Broken Card", annualFee: "No annual fee", annualFeeAmount: 999,
    joiningFee: "₹500", joiningFeeAmount: 0, highlights: ["Same benefit", "same benefit"],
    sourceUrls: ["http://issuer.example/card"], applyUrl: "https://issuer.example/card",
    verifiedOn: "2026-10-01", imageUrl: "/card.png",
  }];
  const issues = catalogQualityIssues([card], new Date("2026-10-17")).map((item) => item.issue);
  expect(issues).toEqual(expect.arrayContaining([
    "Annual fee text and amount conflict", "Joining fee text and amount conflict",
    "Duplicate benefit statements", "Non-HTTPS source URL",
  ]));
});

test("accepts a complete internally consistent card", () => {
  const card = { id: "good", name: "Good Card", annualFee: "₹999 + GST", annualFeeAmount: 999,
    joiningFee: "No joining fee", joiningFeeAmount: 0, highlights: ["A sourced benefit"],
    sourceUrls: ["https://issuer.example/card"], applyUrl: "https://issuer.example/card",
    verifiedOn: "2026-10-01", imageUrl: "/card.png" };
  expect(catalogQualityIssues([card], new Date("2026-10-17"))).toEqual([]);
});

test("surfaces limited economics coverage for editorial follow-up", () => {
  const card = { id: "thin", name: "Thin Card", annualFee: "No annual fee", annualFeeAmount: 0,
    joiningFee: "No joining fee", joiningFeeAmount: 0, highlights: ["A benefit"],
    sourceUrls: ["https://issuer.example/card"], applyUrl: "https://issuer.example/card",
    verifiedOn: "2026-10-01", imageUrl: "/card.png", economicsProfile: { quality: "limited", coverage: 36 } };
  expect(catalogQualityIssues([card], new Date("2026-10-17")).map((item) => item.issue)).toContain("Limited economics coverage (36%)");
});
