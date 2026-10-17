import React, { act } from "react";
import { createRoot } from "react-dom/client";
import CardExplorer from "./CardExplorer";
import { getCards } from "../api";

jest.mock("../api", () => ({ getCards: jest.fn(), trackApplyClick: jest.fn() }));
let mockCardId;
jest.mock("react-router-dom", () => ({
  Link: ({ to, children, ...props }) => <a href={to} {...props}>{children}</a>,
  useParams: () => ({ cardId: mockCardId }),
}));

global.IS_REACT_ACT_ENVIRONMENT = true;

const cards = [
  {
    id: "cashback-card", name: "Everyday Cashback", issuer: "Alpha Bank", tagline: "Cashback",
    palette: ["#123456", "#345678"], accent: "#fff", network: "Visa", rating: 4,
    annualFee: "₹999 + GST", joiningFee: "₹999 + GST", rewardLine: "5% online cashback",
    highlights: ["Cashback capped at ₹1,000 monthly.", "Fee waived on eligible spend."],
    bestFor: ["cashback", "online"], creditReq: "good", verifiedOn: "2026-10-09",
    applicationsOpen: true, active: true, applyUrl: "https://example.com/apply",
    sourceUrls: ["https://example.com/terms"], termsNote: "Issuer terms apply.",
    affiliateDisclosureRequired: true,
    editorial: {
      summary: "A focused cashback card for regular online spending.",
      idealFor: ["People who prioritise online cashback."], strengths: ["Strong eligible online earn rate."],
      tradeoffs: ["A monthly cashback cap applies."], verdict: "Worth shortlisting for consistent online use.",
      alternatives: [{ id: "travel-card", name: "Travel Plus", reason: "Compare when travel benefits matter more." }],
    },
  },
  {
    id: "travel-card", name: "Travel Plus", issuer: "Beta Bank", tagline: "Travel",
    palette: ["#111827", "#2563eb"], accent: "#fff", network: "Mastercard", rating: 4,
    annualFee: "₹1,500 + GST", joiningFee: "₹1,500 + GST", rewardLine: "Air miles and lounge access",
    highlights: ["Eight lounge visits each year."], bestFor: ["travel"], creditReq: "excellent",
    verifiedOn: "2026-10-09", applicationsOpen: true, active: true, applyUrl: "https://example.com/travel",
  },
];

function changeInput(input, value) {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  setter.call(input, value);
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

describe("CardExplorer", () => {
  let container;
  let root;

  beforeEach(() => {
    mockCardId = undefined;
    localStorage.clear();
    getCards.mockResolvedValue(cards);
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(async () => {
    await act(async () => root.unmount());
    container.remove();
    jest.clearAllMocks();
  });

  test("searches the public catalogue without requiring the quiz", async () => {
    await act(async () => root.render(<CardExplorer />));
    await act(async () => Promise.resolve());
    expect(container.textContent).toContain("2 cards found");
    const search = container.querySelector('input[aria-label="Search cards"]');
    await act(async () => changeInput(search, "lounge"));
    expect(container.textContent).toContain("1 card found");
    expect(container.textContent).toContain("Travel Plus");
    expect(container.textContent).not.toContain("Everyday Cashback");
  });

  test("supports a direct link to complete card details", async () => {
    mockCardId = "cashback-card";
    await act(async () => root.render(<CardExplorer />));
    await act(async () => Promise.resolve());
    expect(container.textContent).toContain("Everything we know about this card");
    expect(container.textContent).toContain("Cashback capped at ₹1,000 monthly.");
    expect(container.textContent).toContain("Issuer source 1");
    expect(container.textContent).toContain("may earn a commission");
    expect(container.textContent).toContain("A focused cashback card for regular online spending.");
    expect(container.textContent).toContain("Trade-offs to understand");
    expect(container.textContent).toContain("Worth shortlisting for consistent online use.");
    expect(container.textContent).toContain("Compare before deciding");
    const analysis = Array.from(container.querySelectorAll("h3")).find((item) => item.textContent === "Detailed CardIQ analysis");
    const apply = Array.from(container.querySelectorAll("button")).find((item) => item.textContent.includes("Apply on Alpha Bank"));
    expect(analysis.compareDocumentPosition(apply) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  test("filters by category and compares any two selected cards", async () => {
    await act(async () => root.render(<CardExplorer />));
    await act(async () => Promise.resolve());
    const cashback = Array.from(container.querySelectorAll("button")).find((item) => item.textContent === "Cashback");
    await act(async () => cashback.click());
    expect(container.textContent).toContain("Everyday Cashback");
    expect(container.textContent).not.toContain("Travel Plus");
    const allCards = Array.from(container.querySelectorAll("button")).find((item) => item.textContent === "All cards");
    await act(async () => allCards.click());
    const addButtons = Array.from(container.querySelectorAll("button")).filter((item) => item.textContent.includes("Add to compare"));
    await act(async () => { addButtons[0].click(); addButtons[1].click(); });
    expect(container.textContent).toContain("Compare 2 of 3 cards");
    const compare = Array.from(container.querySelectorAll("button")).find((item) => item.textContent === "Compare");
    await act(async () => compare.click());
    expect(container.textContent).toContain("Compare cards");
    expect(container.textContent).toContain("Everyday Cashback");
    expect(container.textContent).toContain("Travel Plus");
  });

  test("lets a customer mark an existing card before comparing alternatives", async () => {
    await act(async () => root.render(<CardExplorer />));
    await act(async () => Promise.resolve());
    const ownedButtons = Array.from(container.querySelectorAll("button")).filter((item) => item.textContent === "I have this card");
    await act(async () => ownedButtons[0].click());
    expect(localStorage.getItem("ciq_owned_card")).toBe("cashback-card");
    expect(container.textContent).toContain("This is my card");
    expect(container.textContent).toContain("Compare with your card");
    expect(container.textContent).toContain("Your card: Everyday Cashback");
  });
});
