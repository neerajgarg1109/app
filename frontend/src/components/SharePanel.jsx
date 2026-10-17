import React, { useState } from "react";
import { Check, Copy, Share2 } from "lucide-react";
import { cardShareDetails, socialShareUrl } from "../shareLinks";
import { recordProductEvent } from "../productAnalytics";

export default function SharePanel({ card }) {
  const [copied, setCopied] = useState(false);
  const details = cardShareDetails(card);

  const record = (channel) => recordProductEvent("content_shared", null, { card_id: card.id, channel, page_type: "card" });
  const openChannel = (channel) => {
    record(channel);
    window.open(socialShareUrl(channel, details), "_blank", "noopener,noreferrer");
  };
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(details.url);
      setCopied(true);
      record("copy");
      window.setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      setCopied(false);
    }
  };
  const nativeShare = async () => {
    try {
      await navigator.share(details);
      record("native");
    } catch (error) {
      // Closing the native share sheet is not an error the customer needs to see.
    }
  };

  return <section className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
    <div className="flex items-center gap-2"><Share2 className="h-4 w-4" style={{ color: "var(--ciq-teal)" }} /><h3 className="font-display text-sm font-bold">Share this card</h3></div>
    <p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Send its sourced fees, benefits and CardIQ editorial view.</p>
    <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
      <ShareButton label="WhatsApp" onClick={() => openChannel("whatsapp")} primary />
      <ShareButton label="X" onClick={() => openChannel("x")} />
      <ShareButton label="Facebook" onClick={() => openChannel("facebook")} />
      <ShareButton label={copied ? "Copied" : "Copy link"} onClick={copy} icon={copied ? Check : Copy} />
    </div>
    {typeof navigator.share === "function" && <button type="button" onClick={nativeShare} className="mt-2 w-full rounded-xl border py-2 text-xs font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>More sharing options</button>}
  </section>;
}

function ShareButton({ label, onClick, primary = false, icon: Icon }) {
  return <button type="button" onClick={onClick} className="flex items-center justify-center gap-1 rounded-xl border px-2 py-2 text-xs font-semibold" style={{ borderColor: primary ? "var(--ciq-teal-600)" : "var(--ciq-line)", background: primary ? "#e6f5f0" : "#fff", color: primary ? "var(--ciq-teal)" : "var(--ciq-ink)" }}>{Icon && <Icon className="h-3.5 w-3.5" />}{label}</button>;
}
