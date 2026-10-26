import CustomerNav from "./CustomerNav";
import React, { useState } from "react";
import { BellOff, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { unsubscribeCardAlerts } from "../api";
import Logo from "./Logo";

export default function CardAlertUnsubscribe() {
  const token = new URLSearchParams((window.location.hash.split("?")[1] || "")).get("token") || "";
  const [status, setStatus] = useState("idle");
  const unsubscribe = async () => { setStatus("sending"); try { await unsubscribeCardAlerts(token); setStatus("done"); } catch (_) { setStatus("error"); } };
  return <div className="ciq-shell min-h-screen"><header className="ciq-container ciq-container--wide py-5"><Logo size="md" /></header><CustomerNav /><div className="grid min-h-[65vh] place-items-center p-5"><main className="w-full max-w-md rounded-3xl border bg-white p-6 text-center" style={{ borderColor: "var(--ciq-line)" }}><BellOff className="mx-auto mt-6 h-10 w-10" style={{ color: "var(--ciq-teal)" }} /><h1 className="mt-4 font-display text-2xl font-extrabold">Stop card-change alerts?</h1>{status === "done" ? <><p className="mt-2 text-sm">You have been unsubscribed from this alert.</p><Link to="/" className="mt-5 inline-block font-semibold underline">Return home</Link></> : <><p className="mt-2 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>This stops only the alert linked from your email. It does not affect other alerts you created.</p>{status === "error" && <p role="alert" className="mt-3 text-sm" style={{ color: "#a63e38" }}>This link is invalid or the alert is already inactive.</p>}<button disabled={!token || status === "sending"} onClick={unsubscribe} className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl py-3 font-semibold text-white disabled:opacity-50" style={{ background: "var(--ciq-teal-600)" }}>{status === "sending" && <Loader2 className="h-4 w-4 ciq-spin" />}Unsubscribe this alert</button></>}</main></div></div>;
}
