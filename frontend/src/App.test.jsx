import React, { act } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { submitQuiz } from "./api";

jest.mock("./api", () => ({ submitQuiz: jest.fn() }));
jest.mock("react-router-dom", () => ({
  HashRouter: ({ children }) => <>{children}</>,
  Routes: ({ children }) => children.find((child) => child.props.path === "/"),
  Route: ({ element }) => element,
  Link: ({ to, children }) => <a href={to}>{children}</a>,
}));
jest.mock("./productAnalytics", () => ({ recordProductEvent: jest.fn() }));
jest.mock("./components/Landing", () => ({ onStart }) => <button onClick={onStart}>Start quiz</button>);
jest.mock("./components/Quiz", () => ({ onComplete, error }) => <div>
  {error && <p role="alert">{error}</p>}
  <button onClick={() => onComplete({ goal: "cashback" })}>Finish quiz</button>
</div>);
jest.mock("./components/Result", () => ({ onRefine }) => <div><h1>Recommendation ready</h1><button onClick={() => onRefine({ fee: "free" })}>Refine</button></div>);
jest.mock("./components/CustomerFooter", () => () => null);

global.IS_REACT_ACT_ENVIRONMENT = true;

describe("recommendation recovery", () => {
  let container, root;
  beforeEach(async () => {
    jest.useFakeTimers();
    jest.clearAllMocks();
    localStorage.clear();
    window.location.hash = "#/";
    window.scrollTo = jest.fn();
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    await act(async () => root.render(<App />));
    await act(async () => container.querySelector("button").click());
    // The quiz saves these answers before submitting; an outage must not discard them.
    localStorage.setItem("ciq_quiz_progress", JSON.stringify({ step: 5, answers: { goal: "cashback" } }));
  });
  afterEach(async () => {
    await act(async () => root.unmount());
    container.remove();
    jest.useRealTimers();
  });

  test("keeps answers after a service failure and allows a successful retry", async () => {
    submitQuiz.mockRejectedValueOnce(new Error("Network Error"));
    await act(async () => {
      container.querySelector("button").click();
      jest.advanceTimersByTime(450);
    });
    expect(container.textContent).toContain("Please try again");
    expect(JSON.parse(localStorage.getItem("ciq_quiz_progress")).answers.goal).toBe("cashback");
    submitQuiz.mockResolvedValueOnce({ result_id: "retry-result", scored: [{ card: { id: "card" } }] });
    await act(async () => {
      container.querySelector("button").click();
      jest.advanceTimersByTime(450);
    });
    expect(container.textContent).toContain("Recommendation ready");
    expect(localStorage.getItem("ciq_quiz_progress")).toBeNull();
  });

  test("keeps answers when the service returns an empty recommendation", async () => {
    submitQuiz.mockResolvedValueOnce({ scored: [] });
    await act(async () => {
      container.querySelector("button").click();
      jest.advanceTimersByTime(450);
    });
    expect(container.querySelector('[role="alert"]')).not.toBeNull();
    expect(localStorage.getItem("ciq_quiz_progress")).not.toBeNull();
  });

  test("retains the current result if refinement fails", async () => {
    submitQuiz.mockResolvedValueOnce({ result_id: "result", scored: [{ card: { id: "card" } }] });
    await act(async () => {
      container.querySelector("button").click();
      jest.advanceTimersByTime(450);
    });
    submitQuiz.mockRejectedValueOnce(new Error("Network Error"));
    await act(async () => container.querySelector("button").click());
    expect(container.textContent).toContain("Recommendation ready");
    expect(container.querySelector('[role="alert"]').textContent).toContain("previous result is still available");
  });
});
