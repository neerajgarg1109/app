const fs = require("fs");
const path = require("path");

const source = path.resolve(__dirname, "../../backend/cards_catalog.json");
const destination = path.resolve(__dirname, "../public/cards-catalog.json");
const summaryDestination = path.resolve(__dirname, "../public/cards-catalog-summary.json");

const summaryFields = new Set([
  "id", "name", "issuer", "tagline", "network", "palette", "accent", "annualFee", "annualFeeAmount",
  "joiningFee", "joiningFeeAmount", "rewardLine", "bestFor", "feeType", "minSpend", "creditReq", "rating",
  "verifiedOn", "applicationsOpen", "secured", "active", "coBrandPartner", "imageUrl",
  "editorial", "recommendationEligible", "applyUrl", "homepagePlacement",
]);

const cards = JSON.parse(fs.readFileSync(source, "utf8"));
if (!Array.isArray(cards) || cards.length === 0) {
  throw new Error("Backend card catalogue is empty or invalid");
}

fs.writeFileSync(destination, `${JSON.stringify(cards)}\n`, "utf8");
const summaries = cards.map((card) => {
  const summary = Object.fromEntries(Object.entries(card).filter(([key]) => summaryFields.has(key)));
  if (summary.editorial) {
    summary.editorial = summary.editorial.summary ? { summary: summary.editorial.summary } : {};
  }
  return summary;
});
fs.writeFileSync(summaryDestination, `${JSON.stringify(summaries)}\n`, "utf8");
console.log(`Generated static full and summary fallbacks with ${cards.length} cards.`);
