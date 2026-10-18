export function catalogQualityIssues(cards, now = new Date()) {
  const normalizedNames = cards.map((card) => String(card.name || "").trim().toLowerCase());
  return cards.flatMap((card, index) => {
    const issues = [];
    const annualText = String(card.annualFee || "").toLowerCase();
    const joiningText = String(card.joiningFee || "").toLowerCase();
    if (!card.imageUrl) issues.push("Missing card image");
    if (!card.applyUrl && !card.official_apply_url) issues.push("Missing official apply link");
    if (!(card.highlights || []).length) issues.push("No benefit highlights");
    if (!(card.sourceUrls || []).length) issues.push("No issuer sources");
    if (card.economicsProfile?.quality === "limited") issues.push(`Limited economics coverage (${card.economicsProfile.coverage}%)`);
    if (card.verifiedOn && now.getTime() - new Date(card.verifiedOn).getTime() > 180 * 86400000) issues.push("Details need re-verification");
    if (!card.verifiedOn) issues.push("Missing verification date");
    if (normalizedNames.indexOf(normalizedNames[index]) !== index) issues.push("Possible duplicate product");
    if ((/no annual fee|lifetime free/.test(annualText) && Number(card.annualFeeAmount) > 0)
      || (!/no annual fee|lifetime free/.test(annualText) && Number(card.annualFeeAmount) === 0 && /₹|rs\.?/.test(annualText))) issues.push("Annual fee text and amount conflict");
    if ((/no joining fee|lifetime free/.test(joiningText) && Number(card.joiningFeeAmount) > 0)
      || (!/no joining fee|lifetime free|first.year.free/.test(joiningText) && Number(card.joiningFeeAmount) === 0 && /₹|rs\.?/.test(joiningText))) issues.push("Joining fee text and amount conflict");
    if ((card.highlights || []).length !== new Set((card.highlights || []).map((item) => item.trim().toLowerCase())).size) issues.push("Duplicate benefit statements");
    for (const source of card.sourceUrls || []) {
      if (!String(source).startsWith("https://")) issues.push("Non-HTTPS source URL");
    }
    return [...new Set(issues)].map((issue) => ({ card, issue }));
  });
}
