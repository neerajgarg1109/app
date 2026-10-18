// Static quiz and landing content. Card facts and scoring come from the API.

export const QUIZ_QUESTIONS = [
  {
    id: "goal",
    title: "What should this card do best for you?",
    subtitle: "Choose the outcome you would value most over the next year.",
    type: "single",
    options: [
      {
        value: "travel",
        label: "Make travel better",
        perks: ["Flight and hotel rewards", "Lounge access", "Lower international-spend costs"],
      },
      {
        value: "shopping",
        label: "Reward shopping and food",
        perks: ["Online-shopping rewards", "Dining and delivery benefits", "Partner offers"],
      },
      {
        value: "fuel",
        label: "Save on bills and fuel",
        perks: ["Fuel benefits", "Utility-payment rewards", "Everyday-spend value"],
      },
      {
        value: "cashback",
        label: "Cut everyday costs",
        perks: ["Simple cashback", "Fewer reward calculations", "Clear rupee value"],
      },
    ],
  },
  {
    id: "spend",
    title: "About how much would you put on this card each month?",
    subtitle: "A realistic estimate helps us avoid cards whose fees or milestones will not pay off.",
    type: "single",
    options: [
      { value: "low", label: "Under ₹20,000", perks: ["Prioritise low fees and attainable value"] },
      { value: "mid", label: "₹20,000–₹50,000", perks: ["Balance fees, rewards and milestones"] },
      { value: "high", label: "₹50,000–₹1 lakh", perks: ["Consider richer milestone benefits"] },
      { value: "vhigh", label: "More than ₹1 lakh", perks: ["Compare premium benefits and higher fees"] },
    ],
  },
  {
    id: "fee",
    title: "What annual fee are you comfortable paying?",
    subtitle: "We count a fee as worthwhile only when your likely benefits can justify it.",
    type: "single",
    options: [
      { value: "free", label: "₹0 annual fee", perks: ["Show lifetime-free options first"] },
      { value: "worth", label: "A modest fee, if value clearly exceeds it", perks: ["Include practical paid cards"] },
      { value: "premium", label: "A premium fee, for genuinely useful benefits", perks: ["Include high-fee travel and lifestyle cards"] },
    ],
  },
  {
    id: "usage",
    title: "Where would you use this card most?",
    subtitle: "Choose the category likely to receive the largest share of your card spending.",
    type: "single",
    options: [
      { value: "online", label: "Online shopping", perks: ["Marketplaces, brands and digital purchases"] },
      { value: "dining", label: "Dining and food delivery", perks: ["Restaurants, cafés and delivery apps"] },
      { value: "fuel", label: "Fuel and household bills", perks: ["Fuel, electricity, telecom and utilities"] },
      { value: "flights", label: "Flights and hotels", perks: ["Bookings, stays and travel purchases"] },
    ],
  },
  {
    id: "priority",
    title: "Which benefit would most influence your decision?",
    subtitle: "Pick your must-have when two cards otherwise look equally good.",
    type: "single",
    options: [
      { value: "lounge", label: "Useful airport lounge access", perks: ["Prefer attainable access over headline claims"] },
      { value: "rewards", label: "The highest usable reward value", perks: ["Consider earn rates, caps and redemption value"] },
      { value: "forex", label: "Low foreign-currency markup", perks: ["Reduce the cost of overseas spending"] },
      { value: "cashback", label: "Cashback I can understand", perks: ["Prefer direct value over complex points"] },
    ],
  },
  {
    id: "creditRoute",
    title: "Which application route suits you?",
    subtitle: "This helps us include the right type of card without pretending to predict bank approval.",
    type: "single",
    options: [
      { value: "regular", label: "Regular credit card", perks: ["I have an established credit history and stable income"] },
      { value: "secured", label: "FD-backed card", perks: ["I’m new to credit or want better approval odds"] },
      { value: "either", label: "Show me both", perks: ["Compare value without assuming my eligibility"] },
    ],
  },
];

export const TRUST_POINTS = [
  { icon: "ShieldCheck", text: "No sponsored rankings" },
  { icon: "Timer", text: "Issuer details checked and dated" },
  { icon: "BellOff", text: "Contact details are optional" },
];

export const PROBLEMS = [
  { icon: "List", title: "One clear answer", text: "A focused match instead of another overwhelming list." },
  { icon: "TrendingUp", title: "Reasons, not hype", text: "The fit and the trade-off are both explained." },
  { icon: "Database", title: "Facts you can verify", text: "Every card links back to current issuer terms." },
  { icon: "PhoneCall", title: "Privacy by default", text: "Browse and get matched without sharing a phone number." },
];
