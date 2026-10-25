#!/usr/bin/env python3
"""Materialise an editable editorial layer from CardIQ's sourced card facts.

This is a deterministic backfill, not a source of issuer facts. Editors can refine
the resulting fields in Admin without changing fees, rewards or source citations.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "backend" / "cards_catalog.json"

LABELS = {
    "cashback": "straightforward cashback", "shopping": "shopping rewards",
    "online": "online spending", "travel": "travel benefits", "dining": "dining rewards",
    "lounge": "airport lounge access", "rewards": "reward points", "forex": "international spending",
    "fuel": "fuel savings", "grocery": "grocery spending", "upi": "RuPay UPI payments",
    "secured": "building credit with a fixed deposit",
}
LIMITATION = re.compile(r"cap|exclu|limit|markup|not cash|condition|eligible|only|minimum|quarter", re.I)
STRENGTH = re.compile(r"welcome|complimentary|lounge|cashback|reward|waiv|voucher|milestone|insurance", re.I)
NEGATIVE = re.compile(r"^(?:no|not)\b|excluded|exclusion|ineligible|not cash|discontinued", re.I)


def sentence(value):
    value = str(value or "").strip()
    if not value:
        return ""
    return value if value[-1] in ".!?" else value + "."


def natural(items):
    if not items:
        return "its published benefits"
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


def alternatives(card, cards):
    tags = set(card.get("bestFor") or [])
    fee = card.get("annualFeeAmount") or 0
    choices = []
    for candidate in cards:
        if candidate["id"] == card["id"] or candidate.get("active") is False or candidate.get("applicationsOpen") is False:
            continue
        overlap = len(tags & set(candidate.get("bestFor") or []))
        if not overlap:
            continue
        candidate_fee = candidate.get("annualFeeAmount") or 0
        score = overlap * 20 - abs(candidate_fee - fee) / 500
        if candidate.get("issuer") != card.get("issuer"):
            score += 4
        choices.append((score, candidate))
    result = []
    for _, candidate in sorted(choices, key=lambda item: (-item[0], item[1]["name"]))[:2]:
        candidate_fee = candidate.get("annualFeeAmount") or 0
        shared = natural([LABELS.get(tag, tag.replace("-", " ")) for tag in list(tags & set(candidate.get("bestFor") or []))[:2]])
        if candidate_fee < fee:
            reason = f"A lower-fee way to compare similar strengths in {shared}."
        elif candidate_fee > fee:
            reason = f"A higher-fee option to compare for broader benefits around {shared}."
        else:
            reason = f"A similarly priced alternative for comparing {shared}."
        result.append({"id": candidate["id"], "name": candidate["name"], "reason": reason})
    return result


def editorial(card, cards):
    labels = [LABELS.get(tag, tag.replace("-", " ")) for tag in (card.get("bestFor") or [])[:3]]
    audience = natural(labels)
    fee = card.get("annualFeeAmount") or 0
    highlights = [sentence(item) for item in card.get("highlights") or [] if item]
    structured = [
        *[sentence(item) for item in card.get("welcomeBenefits") or []],
        *[sentence(item) for item in card.get("milestoneBenefits") or []],
        *[sentence(item) for item in card.get("loungeBenefits") or []],
    ]
    strengths = [sentence(card.get("rewardLine"))]
    strengths.extend(
        item for item in structured + highlights
        if STRENGTH.search(item) and not NEGATIVE.search(item)
        and (not LIMITATION.search(item) or "lounge" in item.lower() or "waiv" in item.lower())
        and item not in strengths
    )
    strengths = [item for item in strengths if item][:3]

    tradeoffs = [sentence(item) for item in card.get("exclusions") or []]
    tradeoffs.extend(item for item in highlights if LIMITATION.search(item) and item not in tradeoffs)
    if fee:
        tradeoffs.append(f"The ₹{fee:,.0f} annual fee plus GST needs to be justified by benefits you will actually use.")
    if not tradeoffs:
        tradeoffs.append("Reward value depends on eligible merchant categories and the issuer's current terms.")
    tradeoffs = list(dict.fromkeys(tradeoffs))[:3]

    if card.get("secured"):
        summary = f"{card['name']} is a secured card for people building or rebuilding credit while keeping rewards secondary to access."
        verdict = "Consider it when the fixed-deposit route is useful to you; compare the deposit requirement and exit conditions before applying."
    elif fee == 0:
        summary = f"{card['name']} is a no-annual-fee option centred on {audience}."
        verdict = f"A sensible long-term choice when you want {audience} without a recurring membership charge. Check this condition before applying: {tradeoffs[0]}"
    elif fee >= 5000:
        summary = f"{card['name']} is a premium card built around {audience}, with a ₹{fee:,.0f} annual fee before GST."
        verdict = f"Shortlist it only if you can repeatedly use the premium benefits and comfortably recover the fee. Pay particular attention to this condition: {tradeoffs[0]}"
    else:
        summary = f"{card['name']} is a paid card focused on {audience}, charging ₹{fee:,.0f} annually before GST."
        verdict = f"It deserves a place on the shortlist when your normal spending makes {sentence(card.get('rewardLine')).rstrip('.').lower()} valuable enough to clear the fee. Factor in this condition: {tradeoffs[0]}"

    ideal_for = [f"People who prioritise {label}." for label in labels[:2]]
    if card.get("secured"):
        ideal_for.append("Applicants comfortable backing the card with the issuer's required fixed deposit.")
    elif fee == 0:
        ideal_for.append("People who prefer keeping a card without an annual membership cost.")
    else:
        ideal_for.append("People whose normal usage can recover the annual fee through relevant benefits.")

    return {
        "summary": summary,
        "idealFor": ideal_for,
        "strengths": strengths,
        "tradeoffs": tradeoffs,
        "verdict": verdict,
        "alternatives": alternatives(card, cards),
    }


def main():
    cards = json.loads(CATALOG.read_text())
    for card in cards:
        card["editorial"] = editorial(card, cards)
    CATALOG.write_text(json.dumps(cards, indent=2, ensure_ascii=False) + "\n")
    print(f"Materialised editorial content for {len(cards)} cards")


if __name__ == "__main__":
    main()
