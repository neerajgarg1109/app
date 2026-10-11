"""cardIQ catalog seeding and editorial quiz scoring.

Issuer facts and citations live in cards_catalog.json. Scoring attributes are
cardIQ estimates, not issuer underwriting criteria or approval probabilities.
"""

import json
import re
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
        existing = await db.cards.find_one({"id": card["id"]}, {"adminManaged": 1})
        if existing and existing.get("adminManaged"):
            continue
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
_MONTHLY_SPEND = {"low": 12000, "mid": 35000, "high": 75000, "vhigh": 125000}


def _number(value, fallback=0):
    try:
        return max(0, float(value))
    except (TypeError, ValueError):
        return fallback


def _explicit_first_year_benefits(card):
    """Only count rupee amounts explicitly described as gifts/vouchers/memberships."""
    components = []
    for line in [card.get("rewardLine", ""), *card.get("highlights", [])]:
        if not re.search(r"welcome|gift|voucher|membership worth|joining benefit", line, re.I):
            continue
        values = []
        for raw in re.findall(r"(?:₹|Rs\.?\s*)([\d,]+)", line, re.I):
            amount = int(raw.replace(",", ""))
            if 0 < amount <= 50000:
                values.append(amount)
        if values:
            amount = max(values)
            components.append({"label": line, "value": amount})
    # Avoid counting the same advertised amount twice when repeated in highlights.
    unique = []
    for item in components:
        if item["value"] not in {existing["value"] for existing in unique}:
            unique.append(item)
    return unique[:3]


def _fee_waiver_threshold(card):
    text = card.get("annualFee", "")
    match = re.search(r"waiv\w*\s+(?:on|at|after)\s+₹?\s*([\d.]+)\s*(lakh|lac|thousand)?", text, re.I)
    if not match:
        return None
    amount = float(match.group(1))
    unit = (match.group(2) or "").lower()
    return round(amount * (100000 if unit in {"lakh", "lac"} else 1000 if unit == "thousand" else 1))


def _advertised_lounge_visits(card):
    lines = [line for line in card.get("highlights", []) if "lounge" in line.lower()]
    if not lines:
        return 0
    if any("unlimited" in line.lower() for line in lines):
        return 8  # transparent illustration; actual usage is personalized later
    counts = []
    for line in lines:
        counts.extend(int(raw) for raw in re.findall(r"\b(\d{1,2})\b", line) if 0 < int(raw) <= 20)
    return max(counts, default=0)


def recommend_cards(answers, cards, *, include_unavailable=False):
    goal = answers.get("goal")
    usage = answers.get("usage")
    priority = answers.get("priority")
    fee = answers.get("fee")
    spend = answers.get("spend")
    international = answers.get("international")
    credit = answers.get("credit")
    credit_route = answers.get("creditRoute")

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

        # Prefer an application route rather than claiming to predict issuer approval.
        # Keep the former score-band input for historical results and admin previews.
        if credit_route == "secured":
            if card.get("secured"):
                score += 45
                reasons.append("FD-backed route suits your application preference")
            else:
                score -= 30
        elif credit_route == "regular":
            score += 6 if not card.get("secured") else -24
        elif credit and credit in _CREDIT:
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
        monthly_spend = _number(answers.get("monthlySpend"), _MONTHLY_SPEND.get(spend, 35000))
        annual_spend = round(monthly_spend * 12)
        # Conservative editorial range, not a promise: broad spend midpoint × a
        # match-adjusted effective return, less the published annual fee.
        midpoint_rate = 0.006 + (s["confidence"] / 100) * 0.009
        if goal in s["card"].get("bestFor", []):
            midpoint_rate += 0.002
        category_matches = {
            "onlineSpend": {"online", "shopping", "cashback"},
            "diningSpend": {"dining"},
            "travelSpend": {"travel", "flights", "lounge"},
            "fuelSpend": {"fuel", "utilities"},
            "internationalSpend": {"forex", "travel"},
        }
        matched_monthly = sum(
            _number(answers.get(key)) for key, tags in category_matches.items()
            if tags & set(s["card"].get("bestFor", []))
        )
        if monthly_spend:
            midpoint_rate += min(1, matched_monthly / monthly_spend) * 0.006
        low_rate, high_rate = max(0.005, midpoint_rate * 0.7), min(0.025, midpoint_rate * 1.3)
        fee = s["card"].get("annualFeeAmount", 0) or 0
        waiver_threshold = _fee_waiver_threshold(s["card"])
        fee_waived = bool(waiver_threshold and annual_spend >= waiver_threshold)
        effective_fee = 0 if fee_waived else fee
        gross_low = round(annual_spend * low_rate / 100) * 100
        gross_high = round(annual_spend * high_rate / 100) * 100
        explicit = _explicit_first_year_benefits(s["card"])
        explicit_value = sum(item["value"] for item in explicit)
        advertised_lounge_visits = _advertised_lounge_visits(s["card"])
        lounge_visits = round(_number(answers.get("loungeVisits")))
        lounge_value = lounge_visits * 700 if "lounge" in s["card"].get("bestFor", []) else 0
        available_lounge_value = advertised_lounge_visits * 700 if "lounge" in s["card"].get("bestFor", []) else 0
        potential = gross_high + explicit_value + available_lounge_value + (fee if fee_waived else 0)
        s["valueEstimate"] = {
            "annualSpendAssumption": annual_spend,
            "grossLow": gross_low,
            "grossHigh": gross_high,
            "netLow": gross_low + explicit_value + lounge_value - effective_fee,
            "netHigh": gross_high + explicit_value + lounge_value - effective_fee,
            "annualFee": fee,
            "effectiveAnnualFee": effective_fee,
            "feeWaived": fee_waived,
            "feeWaiverThreshold": waiver_threshold,
            "firstYearBenefits": explicit,
            "firstYearBenefitsValue": explicit_value,
            "loungeVisits": lounge_visits,
            "loungeValue": lounge_value,
            "availableLoungeVisits": advertised_lounge_visits,
            "availableLoungeValue": available_lounge_value,
            "headlinePotential": potential,
            "isPersonalized": bool(answers.get("monthlySpend")),
            "methodology": "Editorial scenario using your spending, published fees and only explicitly priced gifts or vouchers. Lounge value uses ₹700 per visit. Actual rewards depend on eligible categories, caps, exclusions and redemption choices.",
        }
    return scored
