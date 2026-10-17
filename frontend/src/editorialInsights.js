const LABELS = {
  cashback: "cashback", shopping: "shopping", online: "online purchases", travel: "travel",
  dining: "dining", lounge: "airport lounge access", rewards: "reward points", forex: "international spending",
  fuel: "fuel", grocery: "groceries", upi: "UPI payments", secured: "building credit",
};

export function editorialInsights(card) {
  const tags = (card.bestFor || []).slice(0, 3).map((tag) => LABELS[tag] || tag.replaceAll("-", " "));
  const audience = naturalList(tags);
  const annualFee = Number(card.annualFeeAmount || 0);
  const feeWaiver = extractSentence(card.annualFee, /waiv/i) || (card.highlights || []).find((item) => /waiv|revers/i.test(item));
  const limitation = (card.highlights || []).find((item) => /cap|exclu|limit|markup|not cash|condition|eligible/i.test(item));

  let verdict = `${card.name} is a practical option for people who prioritise ${audience || "its published reward proposition"}.`;
  if (card.secured) verdict = `${card.name} is primarily worth considering for building credit through a secured or fixed-deposit-backed card.`;
  else if (annualFee === 0) verdict += " Its no-annual-fee structure lowers the cost of keeping it long term.";
  else if (annualFee >= 5000) verdict += " The premium fee makes sense only if you will consistently use its higher-value benefits.";
  else verdict += " The decision should come down to whether your expected rewards comfortably exceed the annual fee.";

  const goodFit = [
    audience ? `Your regular spending includes ${audience}.` : `You value ${card.rewardLine || "the card's core rewards"}.`,
    annualFee === 0 ? "You want to avoid an annual membership charge." : feeWaiver ? `You can realistically meet the published fee-waiver condition: ${cleanSentence(feeWaiver)}` : `You expect to recover the ₹${annualFee.toLocaleString("en-IN")} annual fee through benefits you will actually use.`,
  ];
  if (card.creditReq) goodFit.push(`Your profile is likely to meet the issuer's ${creditLabel(card.creditReq).toLowerCase()} expectations.`);

  const thinkTwice = [];
  if (limitation) thinkTwice.push(cleanSentence(limitation));
  if (annualFee > 0) thinkTwice.push("You would not use the card enough to offset its annual fee and applicable GST.");
  if (!thinkTwice.length) thinkTwice.push("Most of your spending falls outside the card's eligible reward categories.");

  return { verdict, goodFit, thinkTwice: [...new Set(thinkTwice)].slice(0, 2) };
}

function extractSentence(value, pattern) {
  return String(value || "").split(/[.;]/).find((part) => pattern.test(part))?.trim();
}

function cleanSentence(value) {
  const text = String(value || "").trim().replace(/[.;]+$/, "");
  return text ? `${text.charAt(0).toUpperCase()}${text.slice(1)}.` : "";
}

function naturalList(items) {
  if (items.length < 2) return items[0] || "";
  return `${items.slice(0, -1).join(", ")} and ${items.at(-1)}`;
}

function creditLabel(value) {
  return ({ good: "good credit profile", excellent: "excellent credit profile", fair: "fair credit profile", starter: "starter credit profile", new: "new-to-credit profile" })[value] || "issuer eligibility";
}
