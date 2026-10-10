// Static quiz and landing content. Card facts and scoring come from the API.

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
