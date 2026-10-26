import React, { act } from "react";
import { createRoot } from "react-dom/client";
import Quiz from "./Quiz";

jest.mock("react-router-dom", () => ({ Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a> }));

global.IS_REACT_ACT_ENVIRONMENT = true;

function buttonContaining(container, text) {
  return Array.from(container.querySelectorAll("button")).find((button) => button.textContent.includes(text));
}

describe("Quiz journey", () => {
  let container;
  let root;

  beforeEach(() => {
    jest.useFakeTimers();
    localStorage.clear();
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(async () => {
    await act(async () => root.unmount());
    container.remove();
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  async function renderQuiz(props = {}) {
    const defaults = { onComplete: jest.fn(), onExit: jest.fn(), error: null };
    const merged = { ...defaults, ...props };
    await act(async () => root.render(<Quiz {...merged} />));
    return merged;
  }

  async function choose(text) {
    const button = buttonContaining(container, text);
    expect(button).toBeTruthy();
    await act(async () => {
      button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      jest.advanceTimersByTime(361);
    });
  }

  test("automatically advances through all six answers and submits once", async () => {
    const { onComplete } = await renderQuiz();
    expect(container.textContent).toContain("1/6");
    await choose("Make travel better");
    expect(container.textContent).toContain("2/6");
    await choose("₹20,000–₹50,000");
    await choose("A modest fee");
    await choose("Flights and hotels");
    await choose("Useful airport lounge access");
    expect(container.textContent).toContain("6/6");
    expect(container.textContent).toContain("Which application route suits you?");
    await choose("Regular credit card");
    expect(onComplete).toHaveBeenCalledTimes(1);
    expect(onComplete).toHaveBeenCalledWith({
      goal: "travel", spend: "mid", fee: "worth", usage: "flights", priority: "lounge", creditRoute: "regular",
    });
  });

  test("back on the first question exits the quiz", async () => {
    const { onExit } = await renderQuiz();
    const back = container.querySelector("header button");
    await act(async () => back.dispatchEvent(new MouseEvent("click", { bubbles: true })));
    expect(onExit).toHaveBeenCalledTimes(1);
  });

  test("restores saved progress and can move back", async () => {
    localStorage.setItem("ciq_quiz_progress", JSON.stringify({
      step: 2, answers: { goal: "cashback", spend: "low" },
    }));
    await renderQuiz();
    expect(container.textContent).toContain("3/6");
    expect(container.textContent).toContain("What annual fee are you comfortable paying?");
    const back = container.querySelector("header button");
    await act(async () => back.dispatchEvent(new MouseEvent("click", { bubbles: true })));
    expect(container.textContent).toContain("2/6");
  });

  test("shows a matching-service error without blocking answer selection", async () => {
    await renderQuiz({ error: "Matching service unavailable" });
    expect(container.textContent).toContain("Matching service unavailable");
    await choose("Cut everyday costs");
    expect(container.textContent).toContain("2/6");
  });
});
