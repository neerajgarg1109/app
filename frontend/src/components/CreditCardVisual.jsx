import React from "react";
import { Wifi } from "lucide-react";

// Original CSS-rendered credit card (no third-party card art).
export default function CreditCardVisual({ card, floating = false, number = "8841 2290 7756 0194" }) {
  const [c1, c2] = card.palette;
  return (
    <div
      className={`relative w-full rounded-2xl p-5 text-white overflow-hidden ${floating ? "ciq-float" : ""}`}
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

      <div className="relative mt-4 font-mono text-base sm:text-lg tracking-[0.18em] drop-shadow-sm">
        {number}
      </div>

      <div className="relative mt-3 flex items-end justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest opacity-70">Card holder</div>
          <div className="text-sm font-semibold">YOUR NAME</div>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-widest opacity-70">Network</div>
          <div className="text-sm font-semibold">{card.network}</div>
        </div>
      </div>
    </div>
  );
}
