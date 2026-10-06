import { useState, useEffect } from "react";
import "./App.css";
import Landing from "./components/Landing";
import Quiz from "./components/Quiz";
import LeadForm from "./components/LeadForm";
import Result from "./components/Result";
import { submitQuiz } from "./api";
import { Loader2 } from "lucide-react";

const ANALYZE_STEPS = [
  "Reading your answers",
  "Scanning 40+ cards",
  "Filtering out sponsored noise",
  "Locking your best match",
];

function Analyzing() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((x) => (x < ANALYZE_STEPS.length - 1 ? x + 1 : x)), 650);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="ciq-shell grid min-h-screen place-items-center">
      <div className="ciq-container text-center">
        <div className="relative mx-auto grid h-24 w-24 place-items-center">
          <span className="absolute h-24 w-24 rounded-full ciq-ring" style={{ background: "rgba(13,148,136,0.25)" }} />
          <span className="absolute h-24 w-24 rounded-full ciq-ring" style={{ background: "rgba(13,148,136,0.18)", animationDelay: "0.5s" }} />
          <span className="grid h-16 w-16 place-items-center rounded-full text-white" style={{ background: "linear-gradient(140deg,#0d9488,#0f766e)" }}>
            <Loader2 className="h-7 w-7 ciq-spin" />
          </span>
        </div>
        <h2 className="mt-8 font-display text-xl font-extrabold" style={{ color: "var(--ciq-ink)" }}>
          Finding your perfect card…
        </h2>
        <p className="mt-2 text-sm font-medium transition-all" style={{ color: "var(--ciq-teal)" }}>
          {ANALYZE_STEPS[i]}
        </p>
      </div>
    </div>
  );
}

function App() {
  const [screen, setScreen] = useState("landing"); // landing | quiz | lead | analyzing | result
  const [answers, setAnswers] = useState(null);
  const [scored, setScored] = useState(null);
  const [resultId, setResultId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [screen]);

  const handleQuizComplete = (ans) => {
    setAnswers(ans);
    setError(null);
    setScreen("lead");
  };

  const handleLeadSubmit = async (lead) => {
    setSubmitting(true);
    setError(null);
    try {
      const data = await submitQuiz(answers, lead);
      setScored(data.scored);
      setResultId(data.result_id);
      setScreen("analyzing");
      setTimeout(() => setScreen("result"), 2900);
    } catch (e) {
      setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const restart = () => {
    setAnswers(null);
    setScored(null);
    setResultId(null);
    setError(null);
    setScreen("landing");
  };

  return (
    <div className="App">
      {screen === "landing" && <Landing onStart={() => setScreen("quiz")} />}
      {screen === "quiz" && <Quiz onComplete={handleQuizComplete} onExit={restart} />}
      {screen === "lead" && (
        <LeadForm onSubmit={handleLeadSubmit} onBack={() => setScreen("quiz")} submitting={submitting} error={error} />
      )}
      {screen === "analyzing" && <Analyzing />}
      {screen === "result" && scored && (
        <Result scored={scored} resultId={resultId} onRestart={restart} />
      )}
    </div>
  );
}

export default App;
