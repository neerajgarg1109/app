import React from "react";

export default function Logo({ size = "md", onClick }) {
  const dims = size === "lg" ? { box: 40, text: "text-2xl" } : { box: 32, text: "text-xl" };
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 select-none ciq-press"
      aria-label="cardIQ home"
    >
      <span
        className="relative grid place-items-center rounded-xl shadow-sm"
        style={{
          width: dims.box,
          height: dims.box,
          background: "linear-gradient(140deg, #6d5dfc, #4638cc 58%, #12b8aa)",
        }}
      >
        <span
          className="absolute rounded-md"
          style={{
            width: dims.box * 0.42,
            height: dims.box * 0.3,
            background: "linear-gradient(120deg,#ffd166,#ff8f70)",
            top: dims.box * 0.22,
            left: dims.box * 0.2,
            boxShadow: "inset 0 0 0 1px rgba(255,255,255,0.4)",
          }}
        />
      </span>
      <span className={`font-display font-extrabold tracking-tight ${dims.text}`} style={{ color: "var(--ciq-ink)" }}>
        card<span style={{ color: "var(--ciq-teal-600)" }}>IQ</span>
      </span>
    </button>
  );
}
