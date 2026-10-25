import React, { useEffect, useState } from "react";
import { Wifi } from "lucide-react";

const OFFICIAL_CARD_IMAGES = {
  "kotak-kotak-cashback-plus-credit-card": "/cards/kotak-cashback-plus.jpg",
  "axis-scapia-axis-bank-credit-card": "/cards/scapia-axis-bank.jpg",
};

const SIZE_CLASSES = {
  sm: "max-w-[220px]",
  md: "max-w-[320px]",
  lg: "max-w-[380px]",
};

export default function CreditCardVisual({ card, floating = false, size = "md" }) {
  const [c1, c2] = card.palette;
  const imageUrl = card.imageUrl || OFFICIAL_CARD_IMAGES[card.id];
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => setImageFailed(false), [imageUrl]);

  if (imageUrl && !imageFailed) {
    return (
      <div
        className={`relative mx-auto grid w-full place-items-center overflow-hidden rounded-2xl border bg-white ${SIZE_CLASSES[size] || SIZE_CLASSES.md} ${floating ? "ciq-float" : ""}`}
        style={{
          aspectRatio: "1.586 / 1",
          borderColor: "var(--ciq-line)",
          boxShadow: "0 24px 50px -22px rgba(15,26,23,0.35)",
        }}
      >
        <img
          src={imageUrl}
          alt={`${card.name} card`}
          className="absolute inset-0 h-full w-full object-contain p-3"
          onError={() => setImageFailed(true)}
        />
      </div>
    );
  }

  return (
    <div
      className={`relative mx-auto w-full rounded-2xl p-4 text-white overflow-hidden ${SIZE_CLASSES[size] || SIZE_CLASSES.md} ${floating ? "ciq-float" : ""}`}
      style={{
        aspectRatio: "1.586 / 1",
        background: `linear-gradient(135deg, ${c1}, ${c2})`,
        boxShadow: "0 24px 50px -22px rgba(15,26,23,0.55)",
      }}
    >
      {/* sheen */}
      <div
        className="absolute inset-0 opacity-70"
        style={{
          background: `radial-gradient(120% 90% at 85% -10%, ${card.accent}33 0%, transparent 55%)`,
        }}
      />
      <div className="relative flex items-start justify-between">
        <span className="font-display font-bold tracking-wide text-sm/none">
          card<span style={{ color: card.accent }}>IQ</span>
        </span>
        <Wifi className="h-5 w-5 rotate-90 opacity-90" />
      </div>

      {/* chip */}
      <div
        className="relative mt-6 h-8 w-11 rounded-md"
        style={{
          background: "linear-gradient(135deg,#f6d87a,#d4a62a)",
          boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.15)",
        }}
      >
        <div className="absolute inset-x-2 top-1/2 h-px -translate-y-1/2 bg-black/20" />
        <div className="absolute inset-y-1 left-1/2 w-px -translate-x-1/2 bg-black/20" />
      </div>

      <div className="relative mt-4 font-display text-base font-extrabold sm:text-lg drop-shadow-sm">
        {card.name}
      </div>

      <div className="relative mt-3 flex items-end justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest opacity-70">Issuer</div>
          <div className="text-sm font-semibold">{card.issuer}</div>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-widest opacity-70">Network</div>
          <div className="text-sm font-semibold">{card.network}</div>
        </div>
      </div>
    </div>
  );
}
