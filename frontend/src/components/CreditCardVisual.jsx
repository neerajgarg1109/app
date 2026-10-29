import React, { useEffect, useState } from "react";

import catalogArtwork from "../data/cardArtwork.json";

export const getCardArtwork = card => card.imageUrl || catalogArtwork[card.id];

const SIZE_CLASSES = {
  thumbnail: "max-w-[80px]",
  sm: "max-w-[220px]",
  md: "max-w-[320px]",
  lg: "max-w-[380px]",
};

export default function CreditCardVisual({ card, floating = false, size = "md" }) {
  const imageUrl = getCardArtwork(card);
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
          className="absolute inset-0 h-full w-full object-contain"
          loading="lazy"
          decoding="async"
          onError={() => setImageFailed(true)}
        />
      </div>
    );
  }

  return (
    <div className={`mx-auto grid w-full place-items-center rounded-xl border bg-slate-50 p-2 text-center text-xs text-slate-500 ${SIZE_CLASSES[size] || SIZE_CLASSES.md}`} style={{ aspectRatio: "1.586 / 1" }} role="img" aria-label={`${card.name}: official artwork unavailable`}>
      Artwork unavailable
    </div>
  );
}
