import CustomerNav from "./CustomerNav";
import React, { useState } from "react";
import { ArrowLeft, ArrowRight, Loader2, Lock, Mail, User, Phone } from "lucide-react";
import Logo from "./Logo";
import { savePartial } from "../api";

export default function LeadForm({ onSubmit, onBack, submitting, error, answers = {} }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [touched, setTouched] = useState(false);
  const [savedPartial, setSavedPartial] = useState(false);

  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const valid = name.trim().length > 1 && emailValid;

  const maybeSavePartial = () => {
    if (emailValid && !savedPartial) {
      setSavedPartial(true);
      savePartial({
        name: name.trim() || undefined,
        email: email.trim(),
        answers,
        step: Object.keys(answers).length,
      }).catch(() => setSavedPartial(false));
    }
  };

  const handle = () => {
    setTouched(true);
    if (!valid || submitting) return;
    onSubmit({ name: name.trim(), email: email.trim(), phone: phone.trim() || undefined });
  };

  const fieldStyle = { borderColor: "var(--ciq-line)" };

  return (
    <div className="ciq-shell flex min-h-screen flex-col pb-28">
      <header className="ciq-container ciq-container--wide flex items-center justify-between py-5">
        <button onClick={onBack} className="ciq-press grid h-9 w-9 place-items-center rounded-full border bg-white" style={fieldStyle}>
          <ArrowLeft className="h-4 w-4" style={{ color: "var(--ciq-ink)" }} />
        </button>
        <Logo size="md" />
        <span className="w-9" />
      </header>
      <CustomerNav />

      <div className="ciq-container mt-6 flex-1 ciq-fade-up">
        <div className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold" style={{ background: "#e6f5f0", color: "var(--ciq-teal)" }}>
          <Lock className="h-3.5 w-3.5" /> Your details stay private
        </div>
        <h2 className="mt-4 font-display text-[26px] leading-tight font-extrabold" style={{ color: "var(--ciq-ink)" }}>
          Almost there — where should we send your match?
        </h2>
        <p className="mt-2 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>
          We'll show your card right away and can email a copy. No spam calls, ever.
        </p>

        <div className="mt-6 space-y-4">
          <Field icon={User} label="Full name" value={name} onChange={setName} placeholder="e.g. Aarav Sharma" />
          <Field icon={Mail} label="Email" value={email} onChange={setEmail} onBlur={maybeSavePartial} placeholder="you@email.com" type="email"
                 invalid={touched && !emailValid} invalidMsg="Enter a valid email" />
          <Field icon={Phone} label="Phone (optional)" value={phone} onChange={setPhone} placeholder="+91 …" type="tel" />
        </div>

        {error && (
          <p className="mt-4 rounded-xl px-3 py-2 text-sm" style={{ background: "#fdecec", color: "#b4433f" }}>{error}</p>
        )}
      </div>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-white/90 backdrop-blur" style={fieldStyle}>
        <div className="ciq-container py-3">
          <button
            onClick={handle}
            disabled={submitting}
            className="ciq-press inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 text-base font-semibold text-white transition-opacity"
            style={{ background: "var(--ciq-teal-600)", opacity: valid && !submitting ? 1 : 0.55 }}
          >
            {submitting ? (<><Loader2 className="h-5 w-5 ciq-spin" /> Finding your match…</>) : (<>Reveal my card <ArrowRight className="h-5 w-5" /></>)}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ icon: Icon, label, value, onChange, onBlur, placeholder, type = "text", invalid, invalidMsg }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-semibold" style={{ color: "var(--ciq-ink)" }}>{label}</span>
      <span
        className="flex items-center gap-2 rounded-2xl border bg-white px-3.5 py-3"
        style={{ borderColor: invalid ? "#d9534f" : "var(--ciq-line)" }}
      >
        <Icon className="h-4 w-4 flex-shrink-0" style={{ color: "var(--ciq-ink-soft)" }} />
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          placeholder={placeholder}
          className="w-full bg-transparent text-[15px] outline-none"
          style={{ color: "var(--ciq-ink)" }}
        />
      </span>
      {invalid && <span className="mt-1 block text-xs" style={{ color: "#b4433f" }}>{invalidMsg}</span>}
    </label>
  );
}
