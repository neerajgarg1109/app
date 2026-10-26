import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Loader2, ArrowRight } from "lucide-react";
import Result from "./Result";
import { getResult } from "../api";
import CustomerNav from "./CustomerNav";
import Logo from "./Logo";

function ResultStatus({ children }) {
  return <div className="ciq-shell min-h-screen"><header className="ciq-container ciq-container--wide py-5"><Logo size="md" /></header><CustomerNav /><div className="grid min-h-[65vh] place-items-center">{children}</div></div>;
}

export default function SharedResult() {
  const { resultId } = useParams();
  const navigate = useNavigate();
  const [state, setState] = useState("loading"); // loading | ok | error
  const [scored, setScored] = useState(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await getResult(resultId);
        if (!active) return;
        setScored(data.scored);
        setState("ok");
      } catch (e) {
        if (active) setState("error");
      }
    })();
    return () => { active = false; };
  }, [resultId]);

  if (state === "loading") {
    return (
      <ResultStatus>
        <Loader2 className="h-8 w-8 ciq-spin" style={{ color: "var(--ciq-teal-600)" }} />
      </ResultStatus>
    );
  }

  if (state === "error") {
    return (
      <ResultStatus>
        <div className="ciq-container text-center">
          <h2 className="font-display text-2xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>Recommendation not found</h2>
          <p className="mt-2 text-sm" style={{ color: "var(--ciq-ink-soft)" }}>This link may be invalid or expired.</p>
          <button onClick={() => navigate("/")} className="ciq-press mt-6 inline-flex items-center gap-2 rounded-2xl px-5 py-3 text-sm font-semibold text-white" style={{ background: "var(--ciq-teal-600)" }}>
            Take the quiz <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </ResultStatus>
    );
  }

  return (
    <Result scored={scored} resultId={resultId} shared onRestart={() => navigate("/")} />
  );
}
