// cardIQ mock data — frontend only.
// Realistic (but original, generic) Indian credit card demo data + quiz engine.

export const QUIZ_QUESTIONS = [
  {
    id: "goal",
    title: "What do you want your card to reward most?",
    subtitle: "Pick the one that fits your life best.",
    type: "single",
    options: [
      {
        value: "travel",
        label: "Travel",
        perks: ["Airport lounge access", "Airline miles & flight rewards", "Low / zero forex markup"],
      },
      {
        value: "shopping",
        label: "Shopping & Food",
        perks: ["Cashback on Amazon & Flipkart", "Rewards on Swiggy & Zomato", "Extra points online"],
      },
      {
        value: "fuel",
        label: "Bills & Fuel",
        perks: ["Fuel surcharge waiver", "Rewards on utilities & rent", "Cashback on groceries"],
      },
      {
        value: "cashback",
        label: "Flat Cashback",
        perks: ["Simple cashback everywhere", "No category tracking", "Straightforward value"],
      },
    ],
  },
  {
    id: "spend",
    title: "What's your monthly card spend?",
    subtitle: "A rough estimate is fine.",
    type: "single",
    options: [
      { value: "low", label: "Under ₹20,000", perks: ["Starter friendly"] },
      { value: "mid", label: "₹20,000 – ₹50,000", perks: ["Balanced rewards"] },
      { value: "high", label: "₹50,000 – ₹1,00,000", perks: ["Premium perks unlock"] },
      { value: "vhigh", label: "Over ₹1,00,000", perks: ["Top-tier eligibility"] },
    ],
  },
  {
    id: "fee",
    title: "How do you feel about annual fees?",
    subtitle: "Great perks sometimes come with a fee.",
    type: "single",
    options: [
      { value: "free", label: "Lifetime free only", perks: ["Zero annual fee"] },
      { value: "worth", label: "A fee is fine if it's worth it", perks: ["Fee offset by value"] },
      { value: "premium", label: "Happy to pay for premium", perks: ["Luxury benefits"] },
    ],
  },
  {
    id: "usage",
    title: "Where does most of your money go?",
    subtitle: "Choose your biggest spending area.",
    type: "single",
    options: [
      { value: "online", label: "Online shopping", perks: ["E-commerce rewards"] },
      { value: "dining", label: "Dining & food delivery", perks: ["Restaurant & delivery perks"] },
      { value: "fuel", label: "Fuel & utilities", perks: ["Surcharge waivers"] },
      { value: "flights", label: "Flights & hotels", perks: ["Travel rewards"] },
    ],
  },
  {
    id: "priority",
    title: "One perk you'd love the most?",
    subtitle: "This helps us fine-tune your match.",
    type: "single",
    options: [
      { value: "lounge", label: "Airport lounge access", perks: [] },
      { value: "rewards", label: "Maximum reward points", perks: [] },
      { value: "forex", label: "No foreign transaction fees", perks: [] },
      { value: "cashback", label: "Simple cashback", perks: [] },
    ],
  },
  {
    id: "international",
    title: "How often do you spend abroad?",
    subtitle: "Foreign spends and travel change the best fit.",
    type: "single",
    options: [
      { value: "often", label: "Often", perks: ["I travel / shop internationally"] },
      { value: "sometimes", label: "Sometimes", perks: ["A trip or two a year"] },
      { value: "rarely", label: "Rarely / never", perks: ["Mostly domestic spends"] },
    ],
  },
  {
    id: "credit",
    title: "What's your credit score range?",
    subtitle: "We'll only match cards you're likely to get.",
    type: "single",
    options: [
      { value: "excellent", label: "Excellent (750+)", perks: ["Unlocks premium cards"] },
      { value: "good", label: "Good (700\u2013749)", perks: ["Most cards available"] },
      { value: "fair", label: "Fair (650\u2013699)", perks: ["Solid everyday cards"] },
      { value: "new", label: "New to credit", perks: ["Starter-friendly picks"] },
    ],
  },
];

export const CARDS = [
  {
    id: "voyager-infinite",
    name: "Voyager Infinite",
    tagline: "Premium travel, unlocked.",
    network: "Visa Infinite",
    palette: ["#0f172a", "#1e293b"],
    accent: "#38bdf8",
    annualFee: "₹10,000 + GST",
    rewardLine: "5X miles on flights & hotels",
    highlights: [
      "Unlimited domestic & global lounge access",
      "Up to 5X reward miles on travel spends",
      "Zero forex markup worldwide",
      "Complimentary airport transfers",
    ],
    bestFor: ["travel", "flights", "lounge", "forex"],
    feeType: "premium",
    minSpend: "high",
    rating: 4.8,
  },
  {
    id: "skymiles-plus",
    name: "SkyMiles Plus",
    tagline: "Fly more, pay less.",
    network: "Mastercard World",
    palette: ["#155e75", "#0e7490"],
    accent: "#67e8f9",
    annualFee: "₹2,500 (waived on ₹3L spend)",
    rewardLine: "4 miles per ₹100 on airlines",
    highlights: [
      "8 complimentary lounge visits / year",
      "4 air miles per ₹100 on flight bookings",
      "1.5% forex markup (low)",
      "Milestone bonus up to 10,000 miles",
    ],
    bestFor: ["travel", "flights", "lounge"],
    feeType: "worth",
    minSpend: "mid",
    rating: 4.6,
  },
  {
    id: "metrocash-rewards",
    name: "MetroCash Rewards",
    tagline: "Big cashback on everyday shopping.",
    network: "Visa Signature",
    palette: ["#0f766e", "#0d9488"],
    accent: "#5eead4",
    annualFee: "₹999 (waived on ₹2L spend)",
    rewardLine: "5% cashback on Amazon & Flipkart",
    highlights: [
      "5% cashback on Amazon & Flipkart",
      "4% back on Swiggy & Zomato",
      "1% unlimited cashback elsewhere",
      "Quarterly milestone vouchers",
    ],
    bestFor: ["shopping", "online", "rewards"],
    feeType: "worth",
    minSpend: "mid",
    rating: 4.7,
  },
  {
    id: "feast-card",
    name: "Feast Dining Card",
    tagline: "Made for foodies.",
    network: "RuPay Platinum",
    palette: ["#9a3412", "#c2410c"],
    accent: "#fdba74",
    annualFee: "₹500 (waived on ₹1L spend)",
    rewardLine: "10% off on food delivery",
    highlights: [
      "10% instant off on Swiggy & Zomato",
      "Up to 20% at partner restaurants",
      "2X points on online shopping",
      "UPI-linked for quick scan & pay",
    ],
    bestFor: ["shopping", "dining", "rewards"],
    feeType: "worth",
    minSpend: "low",
    rating: 4.5,
  },
  {
    id: "fuelmax",
    name: "FuelMax",
    tagline: "Every litre, rewarded.",
    network: "RuPay Select",
    palette: ["#3f3cbb", "#4f46e5"],
    accent: "#a5b4fc",
    annualFee: "₹499 (waived on ₹1L spend)",
    rewardLine: "1% fuel surcharge waiver + rewards",
    highlights: [
      "Fuel surcharge waiver at all pumps",
      "5% back on utilities & rent payments",
      "4% cashback on groceries",
      "Accepted on UPI apps",
    ],
    bestFor: ["fuel", "cashback"],
    feeType: "worth",
    minSpend: "low",
    rating: 4.4,
  },
  {
    id: "everyday-cashback",
    name: "EveryDay Cashback",
    tagline: "No fuss. Just cashback.",
    network: "Visa Platinum",
    palette: ["#166534", "#15803d"],
    accent: "#86efac",
    annualFee: "Lifetime Free",
    rewardLine: "Flat 2% cashback on everything",
    highlights: [
      "Flat 2% cashback on all spends",
      "No reward points to track",
      "Lifetime free — zero annual fee",
      "Instant cashback credited monthly",
    ],
    bestFor: ["cashback", "online", "fuel"],
    feeType: "free",
    minSpend: "low",
    rating: 4.6,
  },
  {
    id: "prime-rewards",
    name: "Prime Rewards",
    tagline: "Online shopping, supercharged.",
    network: "Mastercard Platinum",
    palette: ["#6d28d9", "#7c3aed"],
    accent: "#c4b5fd",
    annualFee: "₹1,000 (waived on ₹1.5L spend)",
    rewardLine: "10X points on online spends",
    highlights: [
      "10X reward points on online shopping",
      "5X on dining & entertainment",
      "4 lounge visits per year",
      "Easy points-to-cash redemption",
    ],
    bestFor: ["shopping", "online", "rewards"],
    feeType: "worth",
    minSpend: "mid",
    rating: 4.5,
  },
  {
    id: "essentials-rupay",
    name: "Essentials RuPay",
    tagline: "Simple value for daily life.",
    network: "RuPay Classic",
    palette: ["#334155", "#475569"],
    accent: "#cbd5e1",
    annualFee: "Lifetime Free",
    rewardLine: "Rewards on bills & groceries",
    highlights: [
      "Rewards on bill & rent payments",
      "Cashback on groceries & essentials",
      "Lifetime free — zero annual fee",
      "Scan & pay on any UPI app",
    ],
    bestFor: ["fuel", "cashback"],
    feeType: "free",
    minSpend: "low",
    rating: 4.3,
  },
];

// Simple weighted scoring engine.
export function recommendCards(answers) {
  const feeMap = { free: "free", worth: "worth", premium: "premium" };
  const scored = CARDS.map((card) => {
    let score = 0;
    const reasons = [];

    // Goal match (strongest signal)
    if (answers.goal && card.bestFor.includes(answers.goal)) {
      score += 40;
      reasons.push(goalReason(answers.goal));
    }
    // Usage match
    if (answers.usage && card.bestFor.includes(answers.usage)) {
      score += 22;
    }
    // Priority perk match
    if (answers.priority && card.bestFor.includes(answers.priority)) {
      score += 20;
      reasons.push(priorityReason(answers.priority));
    }
    // Fee preference
    if (answers.fee) {
      if (feeMap[answers.fee] === card.feeType) {
        score += 16;
      } else if (answers.fee === "free" && card.feeType !== "free") {
        score -= 18;
      } else if (answers.fee === "premium" && card.feeType === "premium") {
        score += 10;
      }
    }
    // Spend tier
    const tierOrder = { low: 0, mid: 1, high: 2, vhigh: 3 };
    if (answers.spend) {
      const want = tierOrder[answers.spend];
      const need = tierOrder[card.minSpend];
      if (want >= need) score += 10;
      else score -= 12;
    }

    return { card, score, reasons: reasons.filter(Boolean) };
  });

  scored.sort((a, b) => b.score - a.score);
  return scored;
}

function goalReason(goal) {
  switch (goal) {
    case "travel": return "Matches your love for travel perks";
    case "shopping": return "Built for your shopping & food spends";
    case "fuel": return "Great for bills, fuel & utilities";
    case "cashback": return "Gives you simple, flat cashback";
    default: return "";
  }
}

function priorityReason(priority) {
  switch (priority) {
    case "lounge": return "Includes the lounge access you wanted";
    case "rewards": return "Maximises your reward points";
    case "forex": return "Low / zero foreign transaction fees";
    case "cashback": return "Straightforward cashback you asked for";
    default: return "";
  }
}

export const TRUST_POINTS = [
  { icon: "ShieldCheck", text: "Not sponsored by any bank" },
  { icon: "Timer", text: "Takes about 60 seconds" },
  { icon: "BellOff", text: "No spam calls, ever" },
];

export const PROBLEMS = [
  { icon: "List", title: "Endless lists", text: "Hundreds of cards with no real guidance." },
  { icon: "TrendingUp", title: "Biased rankings", text: "Paid placements dressed up as top picks." },
  { icon: "Database", title: "Your data, sold", text: "Details quietly shared with banks." },
  { icon: "PhoneCall", title: "Spam calls", text: "Agents hounding you to take 'that' card." },
];
