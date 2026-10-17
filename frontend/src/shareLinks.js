function publicAppOrigin() {
  const configured = (process.env.REACT_APP_PUBLIC_APP_URL || "").replace(/\/$/, "");
  if (configured) return configured;
  const browserOrigin = typeof window !== "undefined" ? window.location.origin : "";
  return `${browserOrigin}${process.env.PUBLIC_URL || ""}`.replace(/\/$/, "");
}

export function cardShareDetails(card) {
  const url = `${publicAppOrigin()}/cards/${encodeURIComponent(card.id)}/`;
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
