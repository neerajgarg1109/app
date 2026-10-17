import categories from "./cardCategories.json";

describe("SEO card category taxonomy", () => {
  test("uses unique, stable category ids and labels", () => {
    expect(new Set(categories.map(({ id }) => id)).size).toBe(categories.length);
    expect(new Set(categories.map(({ label }) => label)).size).toBe(categories.length);
    categories.forEach(({ id }) => expect(id).toMatch(/^[a-z0-9]+(?:-[a-z0-9]+)*$/));
  });

  test("gives every category substantial, distinct intent copy", () => {
    const descriptions = categories.map(({ description }) => description);
    expect(new Set(descriptions).size).toBe(categories.length);
    descriptions.forEach((description) => expect(description.length).toBeGreaterThan(75));
  });

  test("gives every category at least one explicit matching rule", () => {
    categories.forEach((category) => {
      const rules = [
        category.keywords?.length,
        Object.hasOwn(category, "annualFeeMax"),
        Object.hasOwn(category, "annualFeeMin"),
        category.secured,
        category.creditReq,
        category.coBranded,
        category.fintech,
      ];
      expect(rules.some(Boolean)).toBe(true);
    });
  });
});
