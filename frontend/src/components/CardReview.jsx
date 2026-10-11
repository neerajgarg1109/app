import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Check, Loader2, Star } from "lucide-react";
import Logo from "./Logo";
import { getReviewInvitation, submitCardholderReview } from "../api";

const DIMENSIONS = [
  ["overall", "Overall experience"], ["rewards", "Rewards received"],
  ["redemption", "Ease of redemption"], ["service", "Bank service"],
  ["app_experience", "App experience"], ["acceptance", "Card acceptance"],
];

export default function CardReview() {
  const { token } = useParams();
  const [invite, setInvite] = useState(null);
  const [ratings, setRatings] = useState(Object.fromEntries(DIMENSIONS.map(([key]) => [key, 0])));
  const [holder, setHolder] = useState(false);
  const [comments, setComments] = useState("");
  const [status, setStatus] = useState("loading");

  useEffect(() => { getReviewInvitation(token).then((data) => { setInvite(data); setStatus("ready"); }).catch(() => setStatus("invalid")); }, [token]);
  const submit = async () => {
    setStatus("sending");
    try { await submitCardholderReview(token, { ...ratings, current_holder: holder, comments: comments.trim() || null }); setStatus("sent"); }
    catch (e) { setStatus("error"); }
  };
  const complete = holder && Object.values(ratings).every((value) => value >= 1);

  return <div className="ciq-shell min-h-screen pb-12"><header className="ciq-container py-5"><Logo size="md" /></header><main className="ciq-container">
    {status === "loading" && <div className="grid min-h-[60vh] place-items-center"><Loader2 className="h-7 w-7 ciq-spin" /></div>}
    {status === "invalid" && <div className="rounded-3xl border bg-white p-8 text-center"><h1 className="font-display text-2xl font-extrabold">This review link is unavailable</h1><p className="mt-2 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>It may have expired or already been used.</p></div>}
    {status === "sent" && <div className="rounded-3xl border bg-white p-8 text-center"><span className="mx-auto grid h-12 w-12 place-items-center rounded-full" style={{ background: "#e6f5f0" }}><Check className="h-6 w-6" style={{ color: "var(--ciq-teal)" }} /></span><h1 className="mt-4 font-display text-2xl font-extrabold">Thank you for reviewing your card</h1><p className="mt-2 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>Your review will be checked before it contributes to the community rating.</p></div>}
    {invite && !["sent", "invalid"].includes(status) && <div className="rounded-3xl border bg-white p-5 sm:p-7" style={{ borderColor: "var(--ciq-line)" }}><div className="text-xs font-bold uppercase tracking-wide" style={{ color: "var(--ciq-teal)" }}>Cardholder review</div><h1 className="mt-1 font-display text-2xl font-extrabold">How is {invite.card.name} working for you?</h1><p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{invite.card.issuer} · Your experience helps other customers decide.</p><div className="mt-6 space-y-5">{DIMENSIONS.map(([key, label]) => <div key={key} className="flex flex-wrap items-center justify-between gap-3"><span className="text-sm font-semibold">{label}</span><div className="flex gap-1" aria-label={label}>{[1,2,3,4,5].map((value) => <button key={value} onClick={() => setRatings((current) => ({ ...current, [key]: value }))} aria-label={`${label}: ${value} out of 5`}><Star className={`h-7 w-7 ${value <= ratings[key] ? "fill-current" : ""}`} style={{ color: value <= ratings[key] ? "#f0ad2d" : "#cfd5d1" }} /></button>)}</div></div>)}</div><textarea rows="4" value={comments} onChange={(e) => setComments(e.target.value)} placeholder="What should another customer know? (optional)" className="mt-6 w-full rounded-2xl border p-3 text-sm outline-none" style={{ borderColor: "var(--ciq-line)" }} /><label className="mt-4 flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={holder} onChange={(e) => setHolder(e.target.checked)} /><span>I confirm that I currently hold or have used this card.</span></label>{status === "error" && <p className="mt-3 text-sm" style={{ color: "#b4433f" }}>We couldn’t submit the review. Please check every rating and try again.</p>}<button onClick={submit} disabled={!complete || status === "sending"} className="mt-5 w-full rounded-2xl py-3.5 font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)" }}>{status === "sending" ? "Submitting…" : "Submit cardholder review"}</button><p className="mt-3 text-center text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Reviews are moderated. Issuers cannot edit or suppress ratings.</p></div>}
  </main></div>;
}
