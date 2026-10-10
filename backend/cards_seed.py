"""cardIQ catalog seeding and editorial quiz scoring.

Issuer facts and citations live in cards_catalog.json. Scoring attributes are
cardIQ estimates, not issuer underwriting criteria or approval probabilities.
"""

import json
from pathlib import Path

CARDS = json.loads(Path(__file__).with_name("cards_catalog.json").read_text())

# Archive only the demo IDs shipped by this app. Preserve them for historical
# results, email lookups and admin reports; never remove user-created cards.
DEMO_IDS = (
    "voyager-infinite", "skymiles-plus", "metrocash-rewards", "feast-card",
    "fuelmax", "everyday-cashback", "prime-rewards", "essentials-rupay",
)
CATALOG_QUERY = {"active": {"$ne": False}}
RECOMMENDABLE_QUERY = {
    "active": {"$ne": False},
    "applicationsOpen": {"$ne": False},
    "recommendationEligible": {"$ne": False},
}


async def seed_cards(db):
    """Refresh issuer facts; archive only known demo records after upserts succeed."""
    for card in CARDS:
        await db.cards.update_one({"id": card["id"]}, {"$set": card}, upsert=True)
    await db.cards.update_many(
        {"id": {"$in": list(DEMO_IDS)}}, {"$set": {"active": False}}
    )


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


def recommend_cards(answers, cards, *, include_unavailable=False):
    goal = answers.get("goal")
    usage = answers.get("usage")
    priority = answers.get("priority")
    fee = answers.get("fee")
    spend = answers.get("spend")
    international = answers.get("international")
    credit = answers.get("credit")

    scored = []
    for card in cards:
        # The quiz cannot establish invitation or existing-card eligibility.
        if not include_unavailable and (
            card.get("active") is False
            or card.get("applicationsOpen") is False
            or card.get("recommendationEligible") is False
        ):
            continue
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
                reasons.append(
                    "Low forex for your overseas spends" if "forex" in best_for
                    else "Travel rewards suit your overseas purchases"
                )
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
    # Confidence: map absolute score to a friendly 0-100 (perfect match ~ 130 pts)
    for s in scored:
        s["confidence"] = max(35, min(99, round(s["score"] / 130 * 100)))
    return scored
