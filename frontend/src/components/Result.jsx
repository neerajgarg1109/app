import CustomerNav from "./CustomerNav";
import React, { useEffect, useState } from "react";
import { Check, RotateCcw, Star, ArrowRight, Sparkles, ChevronRight, Mail, Loader2, GitCompare, Share2, ExternalLink, Image as ImageIcon, User, Phone, X, Bookmark, Flag, SlidersHorizontal } from "lucide-react";
import Logo from "./Logo";
import CreditCardVisual, { getCardArtwork } from "./CreditCardVisual";
import Compare from "./Compare";
import CardDetails from "./CardDetails";
import SharePanel from "./SharePanel";
import { attachResultLead, emailResult, trackApplyClick, reportCardInformation, scheduleReviewFollowup, getCommunityRating, submitExperienceFeedback } from "../api";
import { contactNameError, contactPhoneError, contactEmailError } from "../contactValidation";
import { recordProductEvent } from "../productAnalytics";
import { formatCustomerDate } from "../formatDate";

export default function Result({ scored, resultId, answers, refining = false, onRefine, onSaveResult, onRestart, shared = false }) {
  const best = scored[0];
  const alternates = scored.slice(1, 3);
  const card = best.card;
  const applicationsUnavailable = card.active === false || card.applicationsOpen === false;
  const annualFee = getAnnualFeeDisplay(card);
  const cautionHighlight = getCautionHighlight(card);
  const tradeOffs = getTradeOffs(card, cautionHighlight);
  const benefitHighlights = [...new Set([card.rewardLine, ...(card.highlights || [])].filter(Boolean))];

  const [emailState, setEmailState] = useState("idle"); // idle | sending | sent | error
  const [sentTo, setSentTo] = useState("");
  const [showCompare, setShowCompare] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showEmailForm, setShowEmailForm] = useState(false);
  const [emailName, setEmailName] = useState("");
  const [emailAddress, setEmailAddress] = useState("");
  const [emailPhone, setEmailPhone] = useState("");
  const [emailTouched, setEmailTouched] = useState(false);
  const [contactConsent, setContactConsent] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [reportText, setReportText] = useState("");
  const [reportEmail, setReportEmail] = useState("");
  const [reportState, setReportState] = useState("idle");
  const [showValueForm, setShowValueForm] = useState(false);
  const [valueInputs, setValueInputs] = useState({ monthlySpend: "", onlineSpend: "", diningSpend: "", travelSpend: "", fuelSpend: "", internationalSpend: "", loungeVisits: "" });
  const [showHandoff, setShowHandoff] = useState(false);
  const [reviewEmail, setReviewEmail] = useState("");
  const [reviewConsent, setReviewConsent] = useState(false);
  const [handoffState, setHandoffState] = useState("idle");
  const [community, setCommunity] = useState(null);
  const [experienceRating, setExperienceRating] = useState(0);
  const [experienceFeedback, setExperienceFeedback] = useState("");
  const [experienceState, setExperienceState] = useState("idle");
  const [selectedAlternate, setSelectedAlternate] = useState(null);

  useEffect(() => { getCommunityRating(card.id).then(setCommunity).catch(() => {}); }, [card.id]);

  const compareCards = scored.slice(0, 3).map((s) => ({ ...s.card, _confidence: s.confidence, _valueEstimate: s.valueEstimate, _reasons: s.reasons }));

  const handleEmail = async () => {
    if (emailState === "sending" || !resultId) return;
    setEmailTouched(true);
    if (contactNameError(emailName) || contactEmailError(emailAddress) || contactPhoneError(emailPhone) || !contactConsent) return;
    setEmailState("sending");
    try {
      await attachResultLead(resultId, {
        name: emailName.trim(),
        email: emailAddress.trim(),
        phone: emailPhone.trim(),
        contact_consent: true,
      });
      await emailResult(resultId);
      setSentTo(emailAddress.trim());
      setEmailState("sent");
      recordProductEvent("lead_submitted", resultId);
      sessionStorage.setItem(`ciq_contact_prompt_${resultId}`, "submitted");
      setShowEmailForm(false);
    } catch (e) {
      setEmailState("error");
    }
  };

  const dismissContactPrompt = () => {
    if (resultId) sessionStorage.setItem(`ciq_contact_prompt_${resultId}`, "skipped");
    setShowEmailForm(false);
  };

  const handleShare = async () => {
    const url = `${window.location.origin}${process.env.PUBLIC_URL}/#/r/${resultId}`;
    const shareData = { title: "My best card from CardIQ", text: `CardIQ recommended ${card.name} as the best card for my needs`, url };
    try {
      if (navigator.share) {
        await navigator.share(shareData);
        return;
      }
    } catch (e) { /* fall through to copy */ }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2200);
    } catch (e) { /* noop */ }
  };

  const continueToIssuer = async (withReminder = false) => {
    if (applicationsUnavailable || !card.applyUrl) return;
    const target = window.open("", "_blank");
    if (target) target.opener = null;
    setHandoffState("working");
    try {
      if (withReminder) await scheduleReviewFollowup(card.id, reviewEmail, resultId);
      localStorage.setItem("ciq_last_handoff", JSON.stringify({ resultId, cardName: card.name, at: new Date().toISOString(), reviewReminder: withReminder }));
      trackApplyClick(card.id, resultId).catch(() => {});
      recordProductEvent("apply_clicked", resultId);
      if (target) target.location = card.applyUrl; else window.location.href = card.applyUrl;
      setShowHandoff(false);
    } catch (e) {
      if (target) target.close();
      setHandoffState("error");
    }
  };

  const saveResultLocally = () => { onSaveResult?.(card.name); setSaved(true); };
  const submitReport = async () => {
    setReportState("sending");
    try { await reportCardInformation(card.id, reportText, reportEmail); setReportState("sent"); }
    catch (e) { setReportState("error"); }
  };
  const personalizeValue = async () => {
    const monthly = Number(valueInputs.monthlySpend || 0);
    if (monthly <= 0) return;
    const spend = monthly < 20000 ? "low" : monthly <= 50000 ? "mid" : monthly <= 100000 ? "high" : "vhigh";
    await onRefine?.({ ...valueInputs, spend });
    setShowValueForm(false);
  };

  const sendExperienceFeedback = async () => {
    if (!experienceRating || experienceState === "sending") return;
    setExperienceState("sending");
    try {
      await submitExperienceFeedback(experienceRating, experienceFeedback, resultId, card.id);
      setExperienceState("sent");
    } catch (e) {
      setExperienceState("error");
    }
  };

  const [imgState, setImgState] = useState("idle"); // idle | working | done

  const generateShareImage = async () => {
    setImgState("working");
    try {
      const W = 1080, H = 1080;
      const canvas = document.createElement("canvas");
      canvas.width = W; canvas.height = H;
      const ctx = canvas.getContext("2d");

      // background
      ctx.fillStyle = "#f6f7f5";
      ctx.fillRect(0, 0, W, H);

      // Use the issuer artwork in exported results as well as on the page.
      let artwork = null;
      const artworkUrl = getCardArtwork(card);
      if (artworkUrl) {
        artwork = await new Promise(resolve => {
          const image = new Image();
          const timeout = setTimeout(() => resolve(null), 5000);
          image.crossOrigin = "anonymous";
          image.onload = () => { clearTimeout(timeout); resolve(image); };
          image.onerror = () => { clearTimeout(timeout); resolve(null); };
          image.src = artworkUrl;
        });
      }
      if (artwork) {
        const scale = Math.min(900 / artwork.naturalWidth, 470 / artwork.naturalHeight);
        const width = artwork.naturalWidth * scale;
        const height = artwork.naturalHeight * scale;
        ctx.drawImage(artwork, 90 + (900 - width) / 2, 170 + (470 - height) / 2, width, height);
      } else {
        ctx.fillStyle = "#55615c";
        ctx.font = "600 44px Inter, sans-serif";
        ctx.fillText(truncate(card.name, 36), 90, 380);
        ctx.font = "400 30px Inter, sans-serif";
        ctx.fillText("Official artwork unavailable", 90, 435);
      }

      // heading
      ctx.fillStyle = "#0f1a17";
      ctx.font = "800 54px 'Plus Jakarta Sans', sans-serif";
      ctx.fillText("My best card from CardIQ", 90, 740);

      // confidence pill
      ctx.fillStyle = "#0d9488";
      roundRect(ctx, 90, 770, 300, 70, 35); ctx.fill();
      ctx.fillStyle = "#ffffff";
      ctx.font = "700 36px Inter, sans-serif";
      ctx.fillText(`${best.confidence}% match`, 120, 816);

      // benefits
      ctx.fillStyle = "#55615c";
      ctx.font = "500 32px Inter, sans-serif";
      card.highlights.slice(0, 3).forEach((h, i) => {
        ctx.fillStyle = "#0d9488";
        ctx.fillText("\u2713", 92, 910 + i * 54);
        ctx.fillStyle = "#334039";
        ctx.fillText(truncate(h, 46), 140, 910 + i * 54);
      });

      // footer
      ctx.fillStyle = "#9aa39e";
      ctx.font = "500 26px Inter, sans-serif";
      ctx.fillText("Find your perfect credit card \u00b7 cardIQ", 90, 1030);

      const blob = await new Promise((res) => canvas.toBlob(res, "image/png"));
      const file = new File([blob], "cardiq-match.png", { type: "image/png" });

      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({ files: [file], title: "My best card from CardIQ", text: `CardIQ recommended ${card.name} as the best card for my needs` });
      } else {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = "cardiq-match.png";
        document.body.appendChild(a); a.click(); a.remove();
        URL.revokeObjectURL(url);
      }
      setImgState("done");
      setTimeout(() => setImgState("idle"), 2200);
    } catch (e) {
      setImgState("idle");
    }
  };

  return (
    <div className="ciq-shell pb-28">
      <header className="ciq-container ciq-container--wide flex items-center justify-between py-5">
        <Logo size="md" onClick={onRestart} />
        <button onClick={onRestart} className="ciq-press flex items-center gap-1.5 rounded-full border bg-white px-3 py-1.5 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>
          <RotateCcw className="h-3.5 w-3.5" /> {shared ? "Take quiz" : "Retake"}
        </button>
      </header>
      <CustomerNav onHome={onRestart} />

      <section className="ciq-container text-center ciq-fade-up">
        <div className="mx-auto inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold" style={{ background: "#e6f5f0", color: "var(--ciq-teal)" }}>
          <Sparkles className="h-3.5 w-3.5" /> Best suited to your needs
        </div>
        <h1 className="mt-3 font-display text-3xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>{card.name}</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{card.tagline}</p>
        {typeof best.confidence === "number" && (
          <div className="mt-3 inline-flex items-center gap-2 rounded-full border px-3 py-1.5" style={{ borderColor: "var(--ciq-line)", background: "#fff" }}>
            <span className="relative grid h-6 w-6 place-items-center">
              <svg viewBox="0 0 36 36" className="h-6 w-6 -rotate-90">
                <circle cx="18" cy="18" r="15" fill="none" stroke="#eef0ec" strokeWidth="5" />
                <circle cx="18" cy="18" r="15" fill="none" stroke="#0d9488" strokeWidth="5" strokeLinecap="round"
                  strokeDasharray={`${(best.confidence / 100) * 94.2} 94.2`} />
              </svg>
            </span>
            <span className="text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>{best.confidence}% match</span>
          </div>
        )}
      </section>

      <section className="ciq-container mt-6 ciq-pop">
        <CreditCardVisual card={card} />
      </section>

      <section className="ciq-container mt-5">
        <div className="grid grid-cols-2 divide-x overflow-hidden rounded-2xl border bg-white" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="flex min-h-[92px] min-w-0 flex-col justify-center px-4 py-4">
            <div className="text-[10px] font-semibold uppercase tracking-[0.08em]" style={{ color: "var(--ciq-ink-soft)" }}>Annual fee</div>
            <div className="mt-1.5 text-xs font-bold leading-snug" style={{ color: "var(--ciq-ink)" }}>{annualFee}</div>
          </div>
          <div className="flex min-h-[92px] min-w-0 flex-col justify-center px-4 py-4">
            <div className="text-[10px] font-semibold uppercase tracking-[0.08em]" style={{ color: "var(--ciq-ink-soft)" }}>Joining fee</div>
            <div className="mt-1.5 text-xs font-bold leading-snug" style={{ color: "var(--ciq-ink)" }}>{card.joiningFee || "Not specified"}</div>
          </div>
        </div>
        {community?.published && <div className="mt-2 flex items-center justify-between rounded-xl border bg-white px-3 py-2 text-xs" style={{ borderColor: "var(--ciq-line)" }}><span className="font-semibold" style={{ color: "var(--ciq-ink)" }}>Cardholder rating</span><span><strong>{community.overall}/5</strong> · {community.count} approved cardholders</span></div>}

        <RecommendationReasons reasons={best.reasons} tradeOffs={tradeOffs} />

        {best.valueEstimate && <div className="mt-3 overflow-hidden rounded-2xl border bg-white" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="p-4 text-white" style={{ background: "linear-gradient(135deg,#4538c8,#6555ed 55%,#159d9a)" }}>
            <div className="text-xs font-semibold uppercase tracking-wide text-white/75">Estimated first-year value</div>
            <div className="mt-1 font-display text-3xl font-extrabold">Up to {formatRupees(best.valueEstimate.headlinePotential)}</div>
            <div className="mt-1 text-xs text-white/80">Includes estimated rewards and benefits with a clear rupee value. Caps, exclusions and usage conditions apply.</div>
          </div>
          <div className="p-4">
            {!best.valueEstimate.isPersonalized && !shared && <button onClick={() => setShowValueForm(true)} className="ciq-press mt-3 w-full rounded-xl py-2.5 text-sm font-semibold text-white" style={{ background: "var(--ciq-teal-600)" }}>Use my monthly spending</button>}
            <details className={`${best.valueEstimate.isPersonalized ? "" : "mt-3"} rounded-xl border`} style={{ borderColor: "var(--ciq-line)" }}>
              <summary className="cursor-pointer px-3 py-3 text-sm font-semibold" style={{ color: "var(--ciq-ink)" }}>See likely value and full breakdown</summary>
              <div className="border-t px-3 pb-3 pt-3" style={{ borderColor: "var(--ciq-line)" }}>
                <div className="flex items-start justify-between gap-4"><div><div className="font-display text-sm font-bold">{best.valueEstimate.isPersonalized ? "Your likely net value" : "Likely net value at your spend band"}</div><div className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>After the annual fee and based on realistic usage.</div></div><div className="text-right"><div className="font-display text-lg font-extrabold" style={{ color: "var(--ciq-teal)" }}>{formatRupees(best.valueEstimate.netLow)}–{formatRupees(best.valueEstimate.netHigh)}</div><div className="text-[10px] uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>estimated range</div></div></div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <ValuePart label="Rewards estimate" value={`${formatRupees(best.valueEstimate.grossLow)}–${formatRupees(best.valueEstimate.grossHigh)}`} />
                  <ValuePart label="Welcome & milestone value" value={formatRupees(best.valueEstimate.firstYearBenefitsValue)} />
                  <ValuePart label={best.valueEstimate.isPersonalized ? "Your lounge value" : "Available lounge value"} value={formatRupees(best.valueEstimate.isPersonalized ? best.valueEstimate.loungeValue : best.valueEstimate.availableLoungeValue)} />
                  <ValuePart label="Annual fee used" value={best.valueEstimate.feeWaived ? "Waived in this scenario" : formatRupees(best.valueEstimate.effectiveAnnualFee)} />
                </div>
                {best.valueEstimate.netHigh < 1500 && best.valueEstimate.annualFee > 0 && <div className="mt-3 rounded-xl px-3 py-2 text-xs" style={{ background: "#fff8e8", color: "#7a5b00" }}>At this spending level, the measurable value may not justify the fee. Consider the lifetime-free refinement below.</div>}
                <div className="mt-3 text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>Annual card spend used: {formatRupees(best.valueEstimate.annualSpendAssumption)}. {best.valueEstimate.methodology}</div>
                <div className="mt-2 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--ciq-teal)" }}>Estimate quality: {best.valueEstimate.economicsQuality || "limited"} · {best.valueEstimate.economicsCoverage ?? 0}% of benefits have structured values</div>
              </div>
            </details>
          </div>
        </div>}

        {/* action row */}
        <div className={`mt-4 grid ${shared ? "grid-cols-2" : "grid-cols-3"} gap-2.5`}>
          {!shared && <button
            onClick={() => { setEmailState("idle"); setShowEmailForm(true); }}
            disabled={emailState === "sending" || emailState === "sent"}
            className="ciq-press flex items-center justify-center gap-1.5 rounded-2xl border bg-white py-3 text-sm font-semibold"
            style={{ borderColor: emailState === "sent" ? "var(--ciq-teal-600)" : "var(--ciq-line)", color: "var(--ciq-ink)" }}
          >
            {emailState === "sending" && <Loader2 className="h-4 w-4 ciq-spin" />}
            {emailState === "sent" ? (<><Check className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} /> Emailed</>) :
             emailState === "sending" ? "Sending…" : (<><Mail className="h-4 w-4" /> Email</>)}
          </button>}
          <button
            onClick={handleShare}
            className="ciq-press flex items-center justify-center gap-1.5 rounded-2xl border bg-white py-3 text-sm font-semibold"
            style={{ borderColor: copied ? "var(--ciq-teal-600)" : "var(--ciq-line)", color: "var(--ciq-ink)" }}
          >
            {copied ? (<><Check className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} /> Copied</>) : (<><Share2 className="h-4 w-4" /> Share result</>)}
          </button>
          <button
            onClick={() => setShowCompare(true)}
            className="ciq-press flex items-center justify-center gap-1.5 rounded-2xl border bg-white py-3 text-sm font-semibold"
            style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}
          >
            <GitCompare className="h-4 w-4" /> Compare
          </button>
        </div>
        <button
          onClick={generateShareImage}
          disabled={imgState === "working"}
          className="ciq-press mt-2.5 flex w-full items-center justify-center gap-2 rounded-2xl border bg-white py-3 text-sm font-semibold"
          style={{ borderColor: imgState === "done" ? "var(--ciq-teal-600)" : "var(--ciq-line)", color: "var(--ciq-ink)" }}
        >
          {imgState === "working" ? (<><Loader2 className="h-4 w-4 ciq-spin" /> Creating image…</>) :
           imgState === "done" ? (<><Check className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} /> Image ready</>) :
           (<><ImageIcon className="h-4 w-4" /> Share as image</>)}
        </button>
        {!shared && <button onClick={saveResultLocally} className="ciq-press mt-2.5 flex w-full items-center justify-center gap-2 rounded-2xl border bg-white py-3 text-sm font-semibold" style={{ borderColor: saved ? "var(--ciq-teal-600)" : "var(--ciq-line)", color: "var(--ciq-ink)" }}><Bookmark className="h-4 w-4" /> {saved ? "Saved on this device" : "Save this result"}</button>}
        {emailState === "sent" && sentTo && (
          <p className="mt-2 text-center text-xs" style={{ color: "var(--ciq-teal)" }}>Sent to {sentTo}</p>
        )}
        {emailState === "error" && (
          <p className="mt-2 text-center text-xs" style={{ color: "#b4433f" }}>Couldn't send email. Try again.</p>
        )}
        <div className="mt-4"><SharePanel card={card} /></div>

        {!shared && onRefine && <div className="mt-4 rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="flex items-center gap-2"><SlidersHorizontal className="h-4 w-4" style={{ color: "var(--ciq-teal-600)" }} /><div className="font-display text-sm font-bold">Refine this recommendation</div></div>
          <p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Change one priority and recalculate without retaking the quiz.</p>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {[
              ["Only lifetime-free", { fee: "free" }],
              ["Prioritise lounge access", { priority: "lounge", goal: "travel" }],
              ["Prefer lower fees", { fee: "worth" }],
              ["I spend mostly online", { usage: "online", goal: "shopping" }],
            ].map(([label, changes]) => <button key={label} disabled={refining} onClick={() => onRefine(changes)} className="ciq-press rounded-xl border px-3 py-2.5 text-xs font-semibold disabled:opacity-50" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>{refining ? "Recalculating…" : label}</button>)}
          </div>
        </div>}
      </section>

      <section className="ciq-container mt-4">
        <div className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
          <div className="font-display text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>All verified benefits and conditions</div>
          <p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Everything currently recorded in the CardIQ catalogue for this card.</p>
          <ul className="mt-3 space-y-2.5">
            {benefitHighlights.map((h) => (
              <li key={h} className="flex items-start gap-2 text-sm" style={{ color: "var(--ciq-ink)" }}>
                <span className="mt-0.5 grid h-5 w-5 flex-shrink-0 place-items-center rounded-full" style={{ background: "#e6f5f0" }}>
                  <Check className="h-3 w-3" style={{ color: "var(--ciq-teal-600)" }} />
                </span>
                {h}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {alternates.length > 0 && (
        <section className="ciq-container mt-6">
          <div className="font-display text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>Strong alternatives, for comparison</div>
          <div className="mt-3 space-y-3">
            {alternates.map((alt, index) => (
              <button type="button" key={alt.card.id} onClick={() => setSelectedAlternate(alt.card)} className="ciq-press flex w-full items-center gap-3 rounded-2xl border bg-white p-3 text-left" style={{ borderColor: "var(--ciq-line)" }} aria-label={`View full details for ${alt.card.name}`}>
                <div className="w-20 flex-shrink-0"><CreditCardVisual card={alt.card} size="thumbnail" /></div>
                <div className="min-w-0 flex-1">
                  <div className="text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--ciq-teal)" }}>#{index + 2} option · Full details</div>
                  <div className="truncate font-display text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>{alt.card.name}</div>
                  <div className="truncate text-xs" style={{ color: "var(--ciq-ink-soft)" }}>{alt.card.rewardLine}</div>
                </div>
                {typeof alt.confidence === "number" && (
                  <span className="flex-shrink-0 rounded-full px-2 py-0.5 text-xs font-bold" style={{ background: "#e6f5f0", color: "var(--ciq-teal)" }}>{alt.confidence}%</span>
                )}
                <ChevronRight className="h-4 w-4 flex-shrink-0" style={{ color: "var(--ciq-ink-soft)" }} />
              </button>
            ))}
          </div>
        </section>
      )}

      <section className="ciq-container mt-8">
        <div className="rounded-2xl border bg-white p-4 sm:p-5" style={{ borderColor: "var(--ciq-line)" }}>
          {experienceState === "sent" ? (
            <div className="flex items-center gap-3" role="status">
              <span className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full" style={{ background: "#e6f5f0" }}><Check className="h-5 w-5" style={{ color: "var(--ciq-teal-600)" }} /></span>
              <div><div className="font-display text-sm font-bold">Thanks for helping us improve CardIQ.</div><p className="mt-0.5 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Your feedback has been recorded anonymously.</p></div>
            </div>
          ) : (
            <>
              <div className="font-display text-sm font-bold">How was your CardIQ experience?</div>
              <p className="mt-1 text-xs" style={{ color: "var(--ciq-ink-soft)" }}>Rate this recommendation—not the card or issuer.</p>
              <div className="mt-3 flex gap-1" aria-label="Rate your CardIQ experience">
                {[1, 2, 3, 4, 5].map((value) => <button key={value} type="button" onClick={() => { setExperienceRating(value); setExperienceState("idle"); }} aria-label={`${value} out of 5`} className="rounded-lg p-1 focus:outline-none focus:ring-2" style={{ color: value <= experienceRating ? "#f0ad2d" : "#cfd5d1" }}><Star className={`h-7 w-7 ${value <= experienceRating ? "fill-current" : ""}`} /></button>)}
              </div>
              {experienceRating > 0 && <div className="mt-3"><textarea rows="3" maxLength="1500" value={experienceFeedback} onChange={(e) => setExperienceFeedback(e.target.value)} placeholder="What worked well, or what should we improve? (optional)" className="w-full rounded-xl border p-3 text-sm outline-none focus:ring-2" style={{ borderColor: "var(--ciq-line)" }} />{experienceState === "error" && <p className="mt-2 text-xs" style={{ color: "#b4433f" }}>We couldn’t save your feedback. Please try again.</p>}<div className="mt-2 flex items-center justify-between gap-3"><span className="text-[10px]" style={{ color: "var(--ciq-ink-soft)" }}>Anonymous · no contact details required</span><button type="button" onClick={sendExperienceFeedback} disabled={experienceState === "sending"} className="rounded-xl px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)" }}>{experienceState === "sending" ? "Sending…" : "Share feedback"}</button></div></div>}
            </>
          )}
        </div>
      </section>

      {card.verifiedOn && (
        <section className="ciq-container mt-8">
          <div className="rounded-2xl border p-4 text-left text-xs leading-relaxed" style={{ borderColor: "var(--ciq-line)", background: "#f1f3f0", color: "var(--ciq-ink-soft)" }}>
            <div className="font-display text-xs font-bold uppercase tracking-wide" style={{ color: "var(--ciq-ink)" }}>Important information</div>
            <p className="mt-2">Card details checked {formatCustomerDate(card.verifiedOn)}. Joining fee: {card.joiningFee}. {card.termsNote}</p>
            <p className="mt-2">CardIQ ranks fit using your answers and our published catalogue facts. Match scores are editorial estimates—not approval odds, customer reviews or paid placements. The issuing bank alone decides eligibility.</p>
            <p className="mt-2 text-[10px] leading-relaxed">Card images, product names and trademarks belong to their respective owners and are shown only for product identification. CardIQ is a comparison platform and is not endorsed by any issuer unless expressly stated. We may earn a commission from some application links.</p>
            <a href={card.officialApplyUrl || card.applyUrl} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block font-semibold underline" style={{ color: "var(--ciq-teal)" }}>Check current issuer terms</a>
            <button onClick={() => setShowReport(true)} className="ml-4 inline-flex items-center gap-1 font-semibold underline" style={{ color: "var(--ciq-ink-soft)" }}><Flag className="h-3 w-3" /> Report outdated information</button>
          </div>
        </section>
      )}

      <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-white/90 backdrop-blur" style={{ borderColor: "var(--ciq-line)" }}>
        <div className="ciq-container py-3">
          <button onClick={() => setShowHandoff(true)} disabled={applicationsUnavailable} className="ciq-press inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 text-base font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)", boxShadow: "0 16px 30px -14px rgba(13,148,136,0.7)" }}>
            {applicationsUnavailable ? "Applications unavailable" : `Apply on ${card.issuer}`} <ExternalLink className="h-5 w-5" />
          </button>
          {card.affiliateDisclosureRequired && <p className="mt-1.5 text-center text-[9px]" style={{ color: "var(--ciq-ink-soft)" }}>CardIQ may earn a commission. Rankings are unaffected.</p>}
        </div>
      </div>

      {showCompare && <Compare cards={compareCards} onClose={() => setShowCompare(false)} />}
      {selectedAlternate && <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 sm:items-center sm:p-5" role="dialog" aria-modal="true" aria-label={`${selectedAlternate.name} details`} onClick={() => setSelectedAlternate(null)}><div className="max-h-[94vh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-white p-5 sm:rounded-3xl" onClick={(event) => event.stopPropagation()}><div className="sticky top-0 z-10 -mx-1 mb-4 flex items-start justify-between bg-white px-1 pb-2"><div><div className="text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--ciq-teal)" }}>Alternative recommendation</div><div className="font-display text-xl font-extrabold">{selectedAlternate.name}</div><div className="text-sm" style={{ color: "var(--ciq-ink-soft)" }}>{selectedAlternate.issuer}</div></div><button type="button" onClick={() => setSelectedAlternate(null)} className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full border" style={{ borderColor: "var(--ciq-line)" }} aria-label="Close card details"><X className="h-4 w-4" /></button></div><CardDetails card={selectedAlternate} heading="Complete features" compact /></div></div>}
      {showHandoff && <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/35 sm:items-center sm:p-5" onClick={() => handoffState !== "working" && setShowHandoff(false)}><div className="w-full max-w-md rounded-t-3xl bg-white p-5 sm:rounded-3xl" onClick={(e) => e.stopPropagation()}><div className="flex items-start justify-between"><div><h2 className="font-display text-xl font-extrabold">Continue to {card.issuer}</h2><p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>You can apply anonymously, or request one reminder to review the card after 75 days.</p></div><button onClick={() => setShowHandoff(false)} disabled={handoffState === "working"} className="rounded-full border p-2" style={{ borderColor: "var(--ciq-line)" }}><X className="h-4 w-4" /></button></div><button onClick={() => continueToIssuer(false)} disabled={handoffState === "working"} className="mt-5 w-full rounded-2xl border py-3 text-sm font-semibold" style={{ borderColor: "var(--ciq-line)", color: "var(--ciq-ink)" }}>Continue without a reminder</button><div className="my-4 flex items-center gap-3 text-xs" style={{ color: "var(--ciq-ink-soft)" }}><span className="h-px flex-1" style={{ background: "var(--ciq-line)" }} />or<span className="h-px flex-1" style={{ background: "var(--ciq-line)" }} /></div><input type="email" value={reviewEmail} onChange={(e) => setReviewEmail(e.target.value)} placeholder="Email address" className="w-full rounded-2xl border px-3.5 py-3 text-sm outline-none" style={{ borderColor: "var(--ciq-line)" }} /><label className="mt-3 flex items-start gap-2 text-xs" style={{ color: "var(--ciq-ink-soft)" }}><input type="checkbox" className="mt-0.5" checked={reviewConsent} onChange={(e) => setReviewConsent(e.target.checked)} /><span>Email me one review reminder in 75 days. This does not subscribe me to marketing.</span></label>{handoffState === "error" && <p className="mt-2 text-xs" style={{ color: "#b4433f" }}>We couldn’t schedule the reminder. Check the email or continue without one.</p>}<button onClick={() => continueToIssuer(true)} disabled={handoffState === "working" || !reviewConsent || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(reviewEmail)} className="mt-4 w-full rounded-2xl py-3 font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)" }}>{handoffState === "working" ? "Continuing…" : "Set reminder and continue"}</button><p className="mt-3 text-center text-[10px]" style={{ color: "var(--ciq-ink-soft)" }}>The issuer decides approval. CardIQ never asks for card credentials.</p></div></div>}
      {showEmailForm && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/35 p-0 sm:items-center sm:p-5" onClick={() => emailState !== "sending" && dismissContactPrompt()}>
          <div className="w-full max-w-md rounded-t-3xl bg-white p-5 shadow-2xl sm:rounded-3xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-display text-xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>Want your result by email?</h2>
              <p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>Complete these details only if you want us to save and email your result. You can skip this step.</p>
              </div>
              <button onClick={dismissContactPrompt} disabled={emailState === "sending"} aria-label="Close" className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full border" style={{ borderColor: "var(--ciq-line)" }}><X className="h-4 w-4" /></button>
            </div>
            <div className="mt-5 space-y-3">
              <EmailField icon={User} label="Name · Required" value={emailName} onChange={setEmailName} placeholder="Your full name" autoComplete="name" error={emailTouched ? contactNameError(emailName) : ""} />
              <EmailField icon={Phone} label="Mobile number · Required" value={emailPhone} onChange={setEmailPhone} placeholder="10-digit Indian mobile number" type="tel" inputMode="tel" autoComplete="tel" maxLength={16} error={emailTouched ? contactPhoneError(emailPhone) : ""} />
              <EmailField icon={Mail} label="Email · Required" value={emailAddress} onChange={setEmailAddress} placeholder="you@email.com" type="email" inputMode="email" autoComplete="email" maxLength={254} error={emailTouched ? contactEmailError(emailAddress) : ""} />
            </div>
            <label className="mt-4 flex items-start gap-2 text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}><input type="checkbox" className="mt-0.5" checked={contactConsent} onChange={(e) => setContactConsent(e.target.checked)} /><span>I agree that CardIQ may use these details to email my result and contact me about this card application. No unrelated marketing.</span></label>
            {emailState === "error" && <p className="mt-3 text-sm" style={{ color: "#b4433f" }}>Couldn’t send the email. Please try again.</p>}
            <button onClick={handleEmail} disabled={emailState === "sending"} className="ciq-press mt-5 inline-flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 font-semibold text-white" style={{ background: "var(--ciq-teal-600)" }}>
              {emailState === "sending" ? <><Loader2 className="h-5 w-5 ciq-spin" /> Saving…</> : <><Mail className="h-5 w-5" /> Save and email my result</>}
            </button>
            <button onClick={dismissContactPrompt} disabled={emailState === "sending"} className="mt-3 w-full py-2 text-sm font-semibold underline" style={{ color: "var(--ciq-ink-soft)" }}>Skip and continue without sharing details</button>
            {emailTouched && !contactConsent && <p className="mt-1 text-center text-xs" style={{ color: "#b4433f" }}>Please confirm how we may use your details, or continue without sharing them.</p>}
            <p className="mt-2 text-center text-[10px] leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>Your details are used only for this result and card-application follow-up. You can withdraw consent by replying to our message.</p>
          </div>
        </div>
      )}
      {showValueForm && <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/35 sm:items-center sm:p-5" onClick={() => setShowValueForm(false)}><div className="max-h-[92vh] w-full max-w-md overflow-y-auto rounded-t-3xl bg-white p-5 sm:rounded-3xl" onClick={(e) => e.stopPropagation()}><div className="flex items-start justify-between"><div><h2 className="font-display text-xl font-extrabold">Calculate your value</h2><p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>No contact details required. Approximate monthly amounts are enough.</p></div><button onClick={() => setShowValueForm(false)} className="rounded-full border p-2" style={{ borderColor: "var(--ciq-line)" }}><X className="h-4 w-4" /></button></div><div className="mt-5 grid grid-cols-2 gap-3"><ValueInput label="Total card spend" value={valueInputs.monthlySpend} onChange={(value) => setValueInputs((x) => ({ ...x, monthlySpend: value }))} required /><ValueInput label="Online shopping" value={valueInputs.onlineSpend} onChange={(value) => setValueInputs((x) => ({ ...x, onlineSpend: value }))} /><ValueInput label="Dining & delivery" value={valueInputs.diningSpend} onChange={(value) => setValueInputs((x) => ({ ...x, diningSpend: value }))} /><ValueInput label="Travel" value={valueInputs.travelSpend} onChange={(value) => setValueInputs((x) => ({ ...x, travelSpend: value }))} /><ValueInput label="Fuel & utilities" value={valueInputs.fuelSpend} onChange={(value) => setValueInputs((x) => ({ ...x, fuelSpend: value }))} /><ValueInput label="International" value={valueInputs.internationalSpend} onChange={(value) => setValueInputs((x) => ({ ...x, internationalSpend: value }))} /><ValueInput label="Lounge visits / year" value={valueInputs.loungeVisits} onChange={(value) => setValueInputs((x) => ({ ...x, loungeVisits: value }))} plain /></div><button disabled={refining || Number(valueInputs.monthlySpend) <= 0} onClick={personalizeValue} className="mt-5 w-full rounded-2xl py-3.5 font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)" }}>{refining ? "Recalculating…" : "Show my personalized value"}</button><p className="mt-3 text-center text-xs" style={{ color: "var(--ciq-ink-soft)" }}>These figures are used only to calculate this recommendation.</p></div></div>}
      {showReport && <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/35 sm:items-center sm:p-5" onClick={() => setShowReport(false)}><div className="w-full max-w-md rounded-t-3xl bg-white p-5 sm:rounded-3xl" onClick={(e) => e.stopPropagation()}><div className="flex items-start justify-between"><div><h2 className="font-display text-xl font-extrabold">Report outdated information</h2><p className="mt-1 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>Tell us what changed. We’ll review it against issuer sources.</p></div><button onClick={() => setShowReport(false)} className="rounded-full border p-2" style={{ borderColor: "var(--ciq-line)" }}><X className="h-4 w-4" /></button></div>{reportState === "sent" ? <div className="mt-5 rounded-2xl p-4 text-sm" style={{ background: "#e6f5f0", color: "var(--ciq-teal)" }}>Thank you. Your report has been recorded for review.</div> : <><textarea rows="5" value={reportText} onChange={(e) => setReportText(e.target.value)} placeholder="For example: the annual fee changed on the issuer page…" className="mt-5 w-full rounded-2xl border p-3 text-sm outline-none" style={{ borderColor: "var(--ciq-line)" }} /><input type="email" value={reportEmail} onChange={(e) => setReportEmail(e.target.value)} placeholder="Email for follow-up (optional)" className="mt-3 w-full rounded-2xl border p-3 text-sm outline-none" style={{ borderColor: "var(--ciq-line)" }} />{reportState === "error" && <p className="mt-2 text-xs" style={{ color: "#b4433f" }}>Please provide at least 10 characters and a valid optional email.</p>}<button disabled={reportState === "sending" || reportText.trim().length < 10} onClick={submitReport} className="mt-4 w-full rounded-2xl py-3 font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)" }}>{reportState === "sending" ? "Sending…" : "Submit report"}</button></>}</div></div>}
    </div>
  );
}

function EmailField({ icon: Icon, label, value, onChange, placeholder, type = "text", error, ...inputProps }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-semibold" style={{ color: "var(--ciq-ink)" }}>{label}</span>
      <span className="flex items-center gap-2 rounded-2xl border px-3.5 py-3" style={{ borderColor: error ? "#d9534f" : "var(--ciq-line)" }}>
        <Icon className="h-4 w-4" style={{ color: "var(--ciq-ink-soft)" }} />
        <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} aria-invalid={Boolean(error)} className="w-full bg-transparent text-sm outline-none" {...inputProps} />
      </span>
      {error && <span className="mt-1 block text-xs" style={{ color: "#b4433f" }}>{error}</span>}
    </label>
  );
}

function RecommendationReasons({ reasons = [], tradeOffs = [] }) {
  if (!reasons.length && !tradeOffs.length) return null;
  return <div className="mt-4 rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ciq-line)" }}>
    <div className="font-display text-sm font-bold" style={{ color: "var(--ciq-ink)" }}>Why this card is your top match</div>
    <ul className="mt-2 space-y-1.5">
      {reasons.slice(0, 3).map((reason) => <li key={reason} className="flex items-start gap-2 text-sm" style={{ color: "var(--ciq-ink-soft)" }}><Check className="mt-0.5 h-4 w-4 flex-shrink-0" style={{ color: "var(--ciq-teal-600)" }} /> {reason}</li>)}
    </ul>
    {tradeOffs.length > 0 && <div className="mt-3 rounded-xl px-3 py-2.5 text-sm leading-relaxed" style={{ background: "#fff8e8", color: "var(--ciq-ink)" }}>
      <div className="font-bold" style={{ color: "#7a5b00" }}>Worth knowing</div>
      <ul className="mt-1.5 space-y-1.5">{tradeOffs.map((note) => <li key={note} className="flex items-start gap-2"><span className="mt-[0.55em] h-1 w-1 flex-shrink-0 rounded-full" style={{ background: "#9a7400" }} /><span>{note}</span></li>)}</ul>
    </div>}
  </div>;
}

function formatRupees(value) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value || 0);
}

function ValuePart({ label, value }) {
  return <div className="rounded-xl p-2.5" style={{ background: "#f7f8f6" }}><div className="text-[10px] uppercase tracking-wide" style={{ color: "var(--ciq-ink-soft)" }}>{label}</div><div className="mt-1 font-bold" style={{ color: "var(--ciq-ink)" }}>{value}</div></div>;
}

function ValueInput({ label, value, onChange, required, plain }) {
  return <label className="text-xs font-semibold">{label}{required && " *"}<div className="mt-1 flex items-center rounded-xl border px-3 py-2.5" style={{ borderColor: "var(--ciq-line)" }}>{!plain && <span className="mr-1" style={{ color: "var(--ciq-ink-soft)" }}>₹</span>}<input type="number" min="0" value={value} onChange={(e) => onChange(e.target.value)} className="w-full bg-transparent text-sm outline-none" placeholder="0" /></div></label>;
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function truncate(str, n) {
  return str.length > n ? str.slice(0, n - 1) + "…" : str;
}

function getAnnualFeeDisplay(card) {
  return (card.annualFee || "Not specified")
    .replace(/\s*\([^)]*\bwaiv(?:e|ed|er)[^)]*\)\s*/i, " ")
    .trim();
}

function getFeeWaiverNote(card) {
  const match = (card.annualFee || "").match(/\(([^)]*\bwaiv(?:e|ed|er)[^)]*)\)/i);
  if (!match) return null;
  const condition = match[1].trim().replace(/^annual fee\s+/i, "");
  return `Annual fee is ${condition.charAt(0).toLowerCase()}${condition.slice(1)}.`;
}

function getCautionHighlight(card) {
  return (card.highlights || []).find((item) => /cap|limit|exclude|minimum|waiv|markup|not cash|only/i.test(item));
}

function getTradeOffs(card, caution) {
  const notes = [getFeeWaiverNote(card), caution].filter(Boolean);
  if (notes.length) return [...new Set(notes)];
  if (card.annualFeeAmount > 0) return [`This card charges ${card.annualFee}; make sure the benefits outweigh the fee for you.`];
  return [card.termsNote || "Rewards depend on eligible transactions and the issuer’s current terms."];
}
