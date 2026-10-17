const PUBLIC_APP_ORIGIN = "https://neerajgarg1109.github.io/app";

export function cardShareDetails(card) {
  const url = `${PUBLIC_APP_ORIGIN}/cards/${encodeURIComponent(card.id)}/`;
  const text = `${card.name} by ${card.issuer}: ${card.rewardLine || "fees, benefits and important conditions"} — reviewed on CardIQ`;
  return { title: `${card.name} | CardIQ`, text, url };
}

export function socialShareUrl(channel, details) {
  const url = encodeURIComponent(details.url);
  const text = encodeURIComponent(details.text);
  if (channel === "whatsapp") return `https://wa.me/?text=${text}%20${url}`;
  if (channel === "x") return `https://twitter.com/intent/tweet?text=${text}&url=${url}`;
  if (channel === "facebook") return `https://www.facebook.com/sharer/sharer.php?u=${url}`;
  throw new Error(`Unsupported share channel: ${channel}`);
}
