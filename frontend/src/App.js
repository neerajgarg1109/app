import { useState, useEffect } from "react";
import "./App.css";
import { HashRouter, Routes, Route } from "react-router-dom";
import Landing from "./components/Landing";
import Quiz from "./components/Quiz";
import Result from "./components/Result";
import SharedResult from "./components/SharedResult";
import Admin from "./components/Admin";
import CardReview from "./components/CardReview";
import CardExplorer from "./components/CardExplorer";
import ValueCalculator from "./components/ValueCalculator";
import IssuerHelp from "./components/IssuerHelp";
import CardAlerts from "./components/CardAlerts";
import CardAlertUnsubscribe from "./components/CardAlertUnsubscribe";
import PurchaseOptimizer from "./components/PurchaseOptimizer";
import CardUpdates from "./components/CardUpdates";
import RestrictedCards from "./components/RestrictedCards";
import CustomerFooter from "./components/CustomerFooter";
import { submitQuiz } from "./api";
import { Loader2 } from "lucide-react";
import { recordProductEvent } from "./productAnalytics";

const ANALYZE_STEPS = [
  "Understanding your priorities and spending",
  "Comparing fees and waiver thresholds",
  "Checking reward caps and exclusions",
  "Reviewing eligibility indicators",
  "Choosing your best card option",
];

function Analyzing() {
  const [i, setI] = useState(0);
  const [waking, setWaking] = useState(false);
  useEffect(() => {
    const t = setInterval(() => setI((x) => (x < ANALYZE_STEPS.length - 1 ? x + 1 : x)), 650);
    const slow = setTimeout(() => setWaking(true), 6000);
    return () => { clearInterval(t); clearTimeout(slow); };
  }, []);
  return (
    <div className="ciq-shell grid min-h-screen place-items-center">
      <div className="ciq-container text-center">
        <div className="relative mx-auto grid h-24 w-24 place-items-center">
          <span className="absolute h-24 w-24 rounded-full ciq-ring" style={{ background: "rgba(13,148,136,0.25)" }} />
          <span className="absolute h-24 w-24 rounded-full ciq-ring" style={{ background: "rgba(13,148,136,0.18)", animationDelay: "0.5s" }} />
          <span className="grid h-16 w-16 place-items-center rounded-full text-white" style={{ background: "linear-gradient(140deg,#6d5dfc,#4538c8 60%,#12b8aa)" }}>
            <Loader2 className="h-7 w-7 ciq-spin" />
          </span>
        </div>
        <h2 className="mt-8 font-display text-xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>
          Finding the best card for your needs…
        </h2>
        <p className="mt-2 text-sm font-medium transition-all" style={{ color: "var(--ciq-teal)" }}>
          {ANALYZE_STEPS[i]}
        </p>
        {waking && <p className="mx-auto mt-3 max-w-sm text-xs leading-relaxed" style={{ color: "var(--ciq-ink-soft)" }}>This is taking a little longer than usual. We’re still comparing your answers.</p>}
      </div>
    </div>
  );
}

function QuizApp() {
  const [screen, setScreen] = useState("landing"); // landing | quiz | analyzing | result
  const [answers, setAnswers] = useState(null);
  const [scored, setScored] = useState(null);
  const [resultId, setResultId] = useState(null);
  const [error, setError] = useState(null);
  const [refining, setRefining] = useState(false);
  const [savedResult, setSavedResult] = useState(() => {
    try { return JSON.parse(localStorage.getItem("ciq_saved_result") || "null"); } catch (e) { return null; }
  });
  const [savedProgress, setSavedProgress] = useState(() => {
    try { return JSON.parse(localStorage.getItem("ciq_quiz_progress") || "null"); } catch (e) { return null; }
  });

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [screen]);

  useEffect(() => { recordProductEvent("landing_view"); }, []);

  const clearProgress = () => {
    localStorage.removeItem("ciq_quiz_progress");
    setSavedProgress(null);
  };

  const startFresh = () => {
    clearProgress();
    recordProductEvent("quiz_started");
    setScreen("quiz");
  };

  const exitToLanding = () => {
    // keep saved progress so the user can resume
    try { setSavedProgress(JSON.parse(localStorage.getItem("ciq_quiz_progress") || "null")); } catch (e) {}
    setScreen("landing");
  };

  const handleQuizComplete = async (ans) => {
    setAnswers(ans);
    setError(null);
    setScreen("analyzing");
    try {
      const [data] = await Promise.all([
        submitQuiz(ans),
        new Promise((resolve) => setTimeout(resolve, 450)),
      ]);
      if (!data?.scored?.length) {
        throw new Error("The matching service returned no recommendations.");
      }
      clearProgress();
      setScored(data.scored);
      setResultId(data.result_id);
      recordProductEvent("result_viewed", data.result_id);
      setScreen("result");
    } catch (e) {
      setError("We couldn't reach the recommendation service. Please try again.");
      setScreen("quiz");
    }
  };

  const restart = () => {
    setAnswers(null);
    setScored(null);
    setResultId(null);
    setError(null);
    clearProgress();
    setScreen("landing");
  };

  const refineResult = async (changes) => {
    setError(null);
    setRefining(true);
    try {
      const nextAnswers = { ...answers, ...changes };
      const data = await submitQuiz(nextAnswers);
      if (!data?.scored?.length) throw new Error("No recommendations returned");
      setAnswers(nextAnswers); setScored(data.scored); setResultId(data.result_id);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return true;
    } catch (e) {
      setError("We couldn't update your recommendation. Your previous result is still available. Please try again.");
      return false;
    } finally { setRefining(false); }
  };

  const saveResult = (name) => {
    const saved = { resultId, cardName: name, savedAt: new Date().toISOString() };
    localStorage.setItem("ciq_saved_result", JSON.stringify(saved)); setSavedResult(saved);
  };

  const hasResume = savedProgress && savedProgress.answers && Object.keys(savedProgress.answers).length > 0;

  return (
    <>
      {screen === "landing" && (
        <Landing
          onStart={startFresh}
          onResume={() => setScreen("quiz")}
          resumeStep={hasResume ? (savedProgress.step || 0) + 1 : null}
          savedResult={savedResult}
        />
      )}
      {screen === "quiz" && <Quiz onComplete={handleQuizComplete} onExit={exitToLanding} error={error} />}
      {screen === "analyzing" && <Analyzing />}
      {screen === "result" && scored && (
        <>
          {error && <p role="alert" className="ciq-container px-5 py-4 text-sm">{error}</p>}
          <Result scored={scored} resultId={resultId} answers={answers} refining={refining} onRefine={refineResult} onSaveResult={saveResult} onRestart={restart} />
        </>
      )}
    </>
  );
}

function App() {
  return (
    <div className="App">
      <HashRouter>
        <Routes>
          <Route path="/" element={<QuizApp />} />
          <Route path="/r/:resultId" element={<SharedResult />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/review/:token" element={<CardReview />} />
          <Route path="/cards" element={<CardExplorer />} />
          <Route path="/cards/:cardId" element={<CardExplorer />} />
          <Route path="/calculator" element={<ValueCalculator />} />
          <Route path="/help/issuers" element={<IssuerHelp />} />
          <Route path="/alerts" element={<CardAlerts />} />
          <Route path="/alerts/unsubscribe" element={<CardAlertUnsubscribe />} />
          <Route path="/wallet-optimizer" element={<PurchaseOptimizer />} />
          <Route path="/updates" element={<CardUpdates />} />
          <Route path="/restricted-cards" element={<RestrictedCards />} />
        </Routes>
        <CustomerFooter />
      </HashRouter>
    </div>
  );
}

export default App;
