"""cardIQ catalog seeding and editorial quiz scoring.

Issuer facts and citations live in cards_catalog.json. Scoring attributes are
cardIQ estimates, not issuer underwriting criteria or approval probabilities.
"""

import json
import re
import hashlib
import math
from pathlib import Path
from pymongo import UpdateOne

CARDS = json.loads(Path(__file__).with_name("cards_catalog.json").read_text())
CATALOG_VERSION = hashlib.sha256(
    json.dumps(CARDS, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()

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
    catalog_ids = [item["id"] for item in CARDS]
    state = await db.catalog_meta.find_one({"_id": "repository_catalog"}, {"version": 1})
    if state and state.get("version") == CATALOG_VERSION:
        present = await db.cards.count_documents({"id": {"$in": catalog_ids}})
        if present == len(CARDS):
            await db.cards.update_many(
                {"id": {"$in": list(DEMO_IDS)}}, {"$set": {"active": False}}
            )
            return

    # Render can cold-start while MongoDB is remote. One find plus one unordered
    # bulk write avoids two network round trips for every catalogue card.
    managed_ids = {
        card["id"]
        async for card in db.cards.find(
            {"id": {"$in": catalog_ids}, "adminManaged": True},
            {"id": 1},
        )
    }
    operations = [
        UpdateOne({"id": card["id"]}, {"$set": card}, upsert=True)
        for card in CARDS
        if card["id"] not in managed_ids
    ]
    if operations:
        await db.cards.bulk_write(operations, ordered=False)
    await db.catalog_meta.update_one(
        {"_id": "repository_catalog"},
        {"$set": {"version": CATALOG_VERSION, "cardCount": len(CARDS)}},
        upsert=True,
    )
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
        number = float(value)
        return max(0, number) if math.isfinite(number) and number <= 12_000_000 else fallback
    except (TypeError, ValueError):
        return fallback


def _explicit_first_year_benefits(card):
    """Only count rupee amounts explicitly described as gifts/vouchers/memberships."""
    components = []
    for line in [card.get("rewardLine", ""), *card.get("highlights", [])]:
        if not re.search(r"welcome|gift|voucher|membership worth|joining benefit", line, re.I):
            continue
        values = []
        for match in re.finditer(r"(?:₹|Rs\.?\s*)([\d,]+)", line, re.I):
            before = line[max(0, match.start() - 45):match.start()]
            after = line[match.end():match.end() + 55].split(".")[0].split(";")[0]
            # A qualifying-spend amount is a condition, never the gift value.
            if re.search(r"(?:on|requires?|spend(?:s|ing)?(?:\s+of)?|purchases?\s+of)\s*$", before, re.I):
                continue
            labelled_before = re.search(r"(?:gift|voucher|membership)(?:\s+worth|\s+of)?\s*$", before, re.I)
            labelled_after = re.match(r"\s*(?:[\w/-]+\s+){0,3}(?:gift|voucher|membership)\b", after, re.I)
            if not (labelled_before or labelled_after):
                continue
            amount = int(match.group(1).replace(",", ""))
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
    match = re.search(r"waiv\w*\s+(?:on|at|after)\s+₹?\s*([\d,]+(?:\.\d+)?)\s*(lakh|lac|thousand)?", text, re.I)
    if not match:
        return None
    amount = float(match.group(1).replace(",", ""))
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


def card_economics_profile(card):
    """Describe which economics inputs are sourced instead of implying false precision."""
    waiver = _fee_waiver_threshold(card)
    lounge_visits = _advertised_lounge_visits(card)
    first_year = _explicit_first_year_benefits(card)
    fields = {
        "annualFee": card.get("annualFeeAmount") is not None,
        "joiningFee": card.get("joiningFeeAmount") is not None,
        "feeWaiver": waiver is not None or (card.get("annualFeeAmount") or 0) == 0,
        "rewardSummary": bool(card.get("rewardLine")),
        "rewardRedemption": bool(card.get("rewardRedemption")),
        "welcomeBenefits": bool(card.get("welcomeBenefits")) or bool(first_year),
        "milestoneBenefits": bool(card.get("milestoneBenefits")),
        "loungeBenefits": bool(card.get("loungeBenefits")) or lounge_visits > 0,
        "exclusions": bool(card.get("exclusions")) or any("exclu" in line.lower() for line in card.get("highlights", [])),
        "forexMarkup": bool(card.get("forexMarkup")) or any("forex" in line.lower() or "foreign" in line.lower() for line in card.get("highlights", [])),
        "fuelBenefits": bool(card.get("fuelBenefits")) or any("fuel" in line.lower() for line in card.get("highlights", [])),
    }
    known = [key for key, value in fields.items() if value]
    missing = [key for key, value in fields.items() if not value]
    coverage = round(len(known) / len(fields) * 100)
    return {
        "coverage": coverage,
        "quality": "high" if coverage >= 80 else "medium" if coverage >= 55 else "limited",
        "knownFields": known,
        "unstructuredFields": missing,
        "feeWaiverThreshold": waiver,
        "advertisedLoungeVisits": lounge_visits,
        "explicitFirstYearBenefits": first_year,
    }


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
        economics = card_economics_profile(s["card"])
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
            "economicsCoverage": economics["coverage"],
            "economicsQuality": economics["quality"],
            "unstructuredEconomicsFields": economics["unstructuredFields"],
            "isPersonalized": bool(answers.get("monthlySpend")),
            "methodology": f'Editorial scenario using your spending and {economics["coverage"]}% structured economics coverage for this card. Published fees and only explicitly priced gifts or vouchers are counted. Lounge value uses ₹700 per visit. Actual rewards depend on eligible categories, caps, exclusions and redemption choices.',
        }
    return scored
