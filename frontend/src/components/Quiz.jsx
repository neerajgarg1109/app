import React, { useState, useEffect } from "react";
import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import Logo from "./Logo";
import { QUIZ_QUESTIONS } from "../mock/mock";

export default function Quiz({ onComplete, onExit }) {
  const saved = (() => {
    try { return JSON.parse(localStorage.getItem("ciq_quiz_progress") || "null"); } catch (e) { return null; }
  })();
  const [step, setStep] = useState(saved?.step || 0);
  const [answers, setAnswers] = useState(saved?.answers || {});
  const q = QUIZ_QUESTIONS[step];
  const total = QUIZ_QUESTIONS.length;
  const selected = answers[q.id];
  const progress = ((step + (selected ? 1 : 0)) / total) * 100;

  useEffect(() => {
    try { localStorage.setItem("ciq_quiz_progress", JSON.stringify({ step, answers })); } catch (e) {}
  }, [step, answers]);

  const select = (value) => {
    setAnswers((a) => ({ ...a, [q.id]: value }));
  };

  const next = () => {
    if (!selected) return;
    if (step === total - 1) {
      onComplete(answers);
    } else {
      setStep((s) => s + 1);
    }
  };

  const back = () => {
    if (step === 0) {
      onExit();
    } else {
      setStep((s) => s - 1);
    }
  };

  return (
    <div className="ciq-shell flex min-h-screen flex-col pb-28">
      <header className="ciq-container flex items-center justify-between py-5">
        <button onClick={back} className="ciq-press grid h-9 w-9 place-items-center rounded-full border bg-white" style={{ borderColor: "var(--ciq-line)" }}>
          <ArrowLeft className="h-4 w-4" style={{ color: "var(--ciq-ink)" }} />
        </button>
        <Logo size="md" onClick={onExit} />
        <span className="text-sm font-semibold" style={{ color: "var(--ciq-ink-soft)" }}>{step + 1}/{total}</span>
      </header>

      <div className="ciq-container">
        <div className="ciq-track"><div className="ciq-track-fill" style={{ width: `${progress}%` }} /></div>
      </div>

      <div key={q.id} className="ciq-container mt-8 flex-1 ciq-fade-up">
        <h2 className="font-display text-[26px] leading-tight font-extrabold" style={{ color: "var(--ciq-ink)" }}>{q.title}</h2>
        <p className="mt-2 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{q.subtitle}</p>

        <div className="mt-6 space-y-3">
          {q.options.map((opt) => {
            const active = selected === opt.value;
            return (
              <button
                key={opt.value}
                onClick={() => select(opt.value)}
                className="ciq-card-hover ciq-press w-full rounded-2xl border bg-white p-4 text-left"
                style={{
                  borderColor: active ? "var(--ciq-teal-600)" : "var(--ciq-line)",
                  boxShadow: active ? "0 0 0 3px rgba(13,148,136,0.15)" : "0 1px 2px rgba(15,26,23,0.04)",
                }}
              >
                <div className="flex items-center justify-between">
                  <span className="font-display text-base font-bold" style={{ color: "var(--ciq-ink)" }}>{opt.label}</span>
                  <span
                    className="grid h-6 w-6 place-items-center rounded-full border-2 transition-colors"
                    style={{
                      borderColor: active ? "var(--ciq-teal-600)" : "#cdd3cf",
                      background: active ? "var(--ciq-teal-600)" : "transparent",
                    }}
                  >
                    {active && <Check className="h-3.5 w-3.5 text-white" />}
                  </span>
                </div>
                {opt.perks && opt.perks.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {opt.perks.map((p) => (
                      <li key={p} className="flex items-center gap-1.5 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>
                        <Check className="h-3 w-3 flex-shrink-0" style={{ color: "var(--ciq-teal-400)" }} /> {p}
                      </li>
                    ))}
                  </ul>
                )}
              </button>
            );
          })}
        </div>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-white/90 backdrop-blur" style={{ borderColor: "var(--ciq-line)" }}>
        <div className="ciq-container py-3">
          <button
            onClick={next}
            disabled={!selected}
            className="ciq-press inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 text-base font-semibold text-white transition-opacity"
            style={{ background: "var(--ciq-teal-600)", opacity: selected ? 1 : 0.45 }}
          >
            {step === total - 1 ? "See my match" : "Continue"} <ArrowRight className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
