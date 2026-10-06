"""cardIQ card catalog + seeding. Single source of truth for card data in MongoDB."""

# NOTE: Cards are realistic DEMO data (original, generic names). applyUrl values are
# placeholder referral links for demonstration (no real bank affiliation).

CARDS = [
    {
        "id": "voyager-infinite",
        "name": "Voyager Infinite",
        "tagline": "Premium travel, unlocked.",
        "network": "Visa Infinite",
        "palette": ["#0f172a", "#1e293b"],
        "accent": "#38bdf8",
        "annualFee": "\u20b910,000 + GST",
        "rewardLine": "5X miles on flights & hotels",
        "highlights": [
            "Unlimited domestic & global lounge access",
            "Up to 5X reward miles on travel spends",
            "Zero forex markup worldwide",
            "Complimentary airport transfers",
        ],
        "bestFor": ["travel", "flights", "lounge", "forex"],
        "feeType": "premium",
        "minSpend": "high",
        "creditReq": "excellent",
        "rating": 4.8,
        "applyUrl": "https://www.example.com/apply/voyager-infinite?ref=cardiq",
    },
    {
        "id": "skymiles-plus",
        "name": "SkyMiles Plus",
        "tagline": "Fly more, pay less.",
        "network": "Mastercard World",
        "palette": ["#155e75", "#0e7490"],
        "accent": "#67e8f9",
        "annualFee": "\u20b92,500 (waived on \u20b93L spend)",
        "rewardLine": "4 miles per \u20b9100 on airlines",
        "highlights": [
            "8 complimentary lounge visits / year",
            "4 air miles per \u20b9100 on flight bookings",
            "1.5% forex markup (low)",
            "Milestone bonus up to 10,000 miles",
        ],
        "bestFor": ["travel", "flights", "lounge"],
        "feeType": "worth",
        "minSpend": "mid",
        "creditReq": "good",
        "rating": 4.6,
        "applyUrl": "https://www.example.com/apply/skymiles-plus?ref=cardiq",
    },
    {
        "id": "metrocash-rewards",
        "name": "MetroCash Rewards",
        "tagline": "Big cashback on everyday shopping.",
        "network": "Visa Signature",
        "palette": ["#0f766e", "#0d9488"],
        "accent": "#5eead4",
        "annualFee": "\u20b9999 (waived on \u20b92L spend)",
        "rewardLine": "5% cashback on Amazon & Flipkart",
        "highlights": [
            "5% cashback on Amazon & Flipkart",
            "4% back on Swiggy & Zomato",
            "1% unlimited cashback elsewhere",
            "Quarterly milestone vouchers",
        ],
        "bestFor": ["shopping", "online", "rewards"],
        "feeType": "worth",
        "minSpend": "mid",
        "creditReq": "good",
        "rating": 4.7,
        "applyUrl": "https://www.example.com/apply/metrocash-rewards?ref=cardiq",
    },
    {
        "id": "feast-card",
        "name": "Feast Dining Card",
        "tagline": "Made for foodies.",
        "network": "RuPay Platinum",
        "palette": ["#9a3412", "#c2410c"],
        "accent": "#fdba74",
        "annualFee": "\u20b9500 (waived on \u20b91L spend)",
        "rewardLine": "10% off on food delivery",
        "highlights": [
            "10% instant off on Swiggy & Zomato",
            "Up to 20% at partner restaurants",
            "2X points on online shopping",
            "UPI-linked for quick scan & pay",
        ],
        "bestFor": ["shopping", "dining", "rewards"],
        "feeType": "worth",
        "minSpend": "low",
        "creditReq": "fair",
        "rating": 4.5,
        "applyUrl": "https://www.example.com/apply/feast-card?ref=cardiq",
    },
    {
        "id": "fuelmax",
        "name": "FuelMax",
        "tagline": "Every litre, rewarded.",
        "network": "RuPay Select",
        "palette": ["#3f3cbb", "#4f46e5"],
        "accent": "#a5b4fc",
        "annualFee": "\u20b9499 (waived on \u20b91L spend)",
        "rewardLine": "1% fuel surcharge waiver + rewards",
        "highlights": [
            "Fuel surcharge waiver at all pumps",
            "5% back on utilities & rent payments",
            "4% cashback on groceries",
            "Accepted on UPI apps",
        ],
        "bestFor": ["fuel", "cashback"],
        "feeType": "worth",
        "minSpend": "low",
        "creditReq": "fair",
        "rating": 4.4,
        "applyUrl": "https://www.example.com/apply/fuelmax?ref=cardiq",
    },
    {
        "id": "everyday-cashback",
        "name": "EveryDay Cashback",
        "tagline": "No fuss. Just cashback.",
        "network": "Visa Platinum",
        "palette": ["#166534", "#15803d"],
        "accent": "#86efac",
        "annualFee": "Lifetime Free",
        "rewardLine": "Flat 2% cashback on everything",
        "highlights": [
            "Flat 2% cashback on all spends",
            "No reward points to track",
            "Lifetime free \u2014 zero annual fee",
            "Instant cashback credited monthly",
        ],
        "bestFor": ["cashback", "online", "fuel"],
        "feeType": "free",
        "minSpend": "low",
        "creditReq": "fair",
        "rating": 4.6,
        "applyUrl": "https://www.example.com/apply/everyday-cashback?ref=cardiq",
    },
    {
        "id": "prime-rewards",
        "name": "Prime Rewards",
        "tagline": "Online shopping, supercharged.",
        "network": "Mastercard Platinum",
        "palette": ["#6d28d9", "#7c3aed"],
        "accent": "#c4b5fd",
        "annualFee": "\u20b91,000 (waived on \u20b91.5L spend)",
        "rewardLine": "10X points on online spends",
        "highlights": [
            "10X reward points on online shopping",
            "5X on dining & entertainment",
            "4 lounge visits per year",
            "Easy points-to-cash redemption",
        ],
        "bestFor": ["shopping", "online", "rewards"],
        "feeType": "worth",
        "minSpend": "mid",
        "creditReq": "good",
        "rating": 4.5,
        "applyUrl": "https://www.example.com/apply/prime-rewards?ref=cardiq",
    },
    {
        "id": "essentials-rupay",
        "name": "Essentials RuPay",
        "tagline": "Simple value for daily life.",
        "network": "RuPay Classic",
        "palette": ["#334155", "#475569"],
        "accent": "#cbd5e1",
        "annualFee": "Lifetime Free",
        "rewardLine": "Rewards on bills & groceries",
        "highlights": [
            "Rewards on bill & rent payments",
            "Cashback on groceries & essentials",
            "Lifetime free \u2014 zero annual fee",
            "Scan & pay on any UPI app",
        ],
        "bestFor": ["fuel", "cashback"],
        "feeType": "free",
        "minSpend": "low",
        "creditReq": "new",
        "rating": 4.3,
        "applyUrl": "https://www.example.com/apply/essentials-rupay?ref=cardiq",
    },
]


async def seed_cards(db):
    """Idempotent upsert of the card catalog (always refresh to latest fields)."""
    for card in CARDS:
        await db.cards.update_one({"id": card["id"]}, {"$set": card}, upsert=True)


# ---- Scoring engine (refined) ----

_GOAL_REASON = {
    "travel": "Matches your love for travel perks",
    "shopping": "Built for your shopping & food spends",
    "fuel": "Great for bills, fuel & utilities",
    "cashback": "Gives you simple, flat cashback",
}
_PRIORITY_REASON = {
    "lounge": "Includes the lounge access you wanted",
    "rewards": "Maximises your reward points",
    "forex": "Low / zero foreign transaction fees",
    "cashback": "Straightforward cashback you asked for",
}
_TIER = {"low": 0, "mid": 1, "high": 2, "vhigh": 3}
_CREDIT = {"new": 0, "fair": 1, "good": 2, "excellent": 3}


def recommend_cards(answers, cards):
    goal = answers.get("goal")
    usage = answers.get("usage")
    priority = answers.get("priority")
    fee = answers.get("fee")
    spend = answers.get("spend")
    international = answers.get("international")
    credit = answers.get("credit")

    scored = []
    for card in cards:
        score = 0
        reasons = []
        best_for = card.get("bestFor", [])

        if goal and goal in best_for:
            score += 40
            reasons.append(_GOAL_REASON.get(goal))
        if usage and usage in best_for:
            score += 22
        if priority and priority in best_for:
            score += 20
            reasons.append(_PRIORITY_REASON.get(priority))

        if fee:
            if fee == card.get("feeType"):
                score += 16
            elif fee == "free" and card.get("feeType") != "free":
                score -= 18
            elif fee == "premium" and card.get("feeType") == "premium":
                score += 10

        if spend is not None and spend in _TIER:
            want = _TIER[spend]
            need = _TIER.get(card.get("minSpend", "low"), 0)
            score += 10 if want >= need else -12

        # International usage boosts forex / travel cards
        if international == "often":
            if any(x in best_for for x in ("forex", "flights", "travel")):
                score += 14
                reasons.append("Low forex for your overseas spends")
        elif international == "rarely":
            if "forex" in best_for:
                score -= 4

        # Credit eligibility gate
        if credit and credit in _CREDIT:
            user_tier = _CREDIT[credit]
            req = _CREDIT.get(card.get("creditReq", "new"), 0)
            if user_tier >= req:
                score += 8
                if req >= 2:
                    reasons.append("Fits your credit profile")
            else:
                score -= 30  # likely not eligible

        # Rating nudges ties
        score += (card.get("rating", 0) - 4.0) * 2

        scored.append({
            "card": card,
            "score": round(score, 2),
            "reasons": [r for r in reasons if r],
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored
