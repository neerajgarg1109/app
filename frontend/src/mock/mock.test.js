import { QUIZ_QUESTIONS } from "./mock";

describe("customer quiz definition", () => {
  test("contains exactly six unique single-choice questions", () => {
    expect(QUIZ_QUESTIONS).toHaveLength(6);
    expect(new Set(QUIZ_QUESTIONS.map((question) => question.id)).size).toBe(6);
    expect(QUIZ_QUESTIONS.every((question) => question.type === "single" && question.options.length >= 3)).toBe(true);
  });

  test("does not ask for a CIBIL band or duplicate international-frequency answer", () => {
    expect(QUIZ_QUESTIONS.map((question) => question.id)).not.toContain("international");
    expect(QUIZ_QUESTIONS.map((question) => question.id)).not.toContain("credit");
    expect(JSON.stringify(QUIZ_QUESTIONS)).not.toMatch(/650|700|750|CIBIL/i);
  });

  test("offers all three application routes", () => {
    const route = QUIZ_QUESTIONS.find((question) => question.id === "creditRoute");
    expect(route.options.map((option) => option.value)).toEqual(["regular", "secured", "either"]);
  });

  test("has unique option values and complete customer-facing copy", () => {
    for (const question of QUIZ_QUESTIONS) {
      expect(question.title.trim()).not.toBe("");
      expect(question.subtitle.trim()).not.toBe("");
      expect(new Set(question.options.map((option) => option.value)).size).toBe(question.options.length);
      expect(question.options.every((option) => option.label.trim() && option.perks.length)).toBe(true);
    }
  });
});
