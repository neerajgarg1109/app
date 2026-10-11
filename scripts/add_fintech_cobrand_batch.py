#!/usr/bin/env python3
"""Add verified consumer credit cards distributed through fintech partners."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "backend" / "cards_catalog.json"
BATCH = "expansion-fintech-cobrand-10-2026-10-11"

# id, issuer, partner, name, official product/apply page, joining, annual,
# annual text suffix, reward summary, tags, network, secured
PRODUCTS = [
    ("sbm-kredit-pe", "SBM Bank India", "Kredit.Pe", "SBM Kredit.Pe Credit Card",
     "https://www.sbm.bank.in/smart_banking/pdf/Kredit-PE-MITC.pdf", 0, 199, None,
     "Cashback and Kredit.Pe rewards on eligible UPI purchases", ["upi", "cashback", "secured"], "RuPay", True),
    ("rbl-salaryse-up", "RBL Bank", "SalarySe", "RBL Bank SalarySe UP Credit Card",
     "https://www.rbl.bank.in/personal-banking/cards/credit-cards/salaryse-up-credit-card", 499, 499,
     "waived on ₹2 lakh eligible annual spend", "Accelerated reward points on eligible UPI payments made through SalarySe",
     ["upi", "rewards", "online"], "RuPay", False),
    ("cub-salaryse-level-up", "City Union Bank", "SalarySe", "CUB SalarySe Level UP Credit Card",
     "https://www.salaryse.com/level-up", 500, 500, "waived on ₹2 lakh eligible annual spend",
     "Accelerated reward points on eligible SalarySe UPI, online and offline purchases",
     ["upi", "rewards", "lounge"], "RuPay", False),
    ("cub-salaryse-level-up-virtual", "City Union Bank", "SalarySe", "CUB SalarySe Level UP Virtual Credit Card",
     "https://www.salaryse.com/level-up", 0, 0, None,
     "Reward points on eligible SalarySe UPI, online and offline purchases",
     ["upi", "rewards", "online"], "RuPay", False),
    ("pnb-zaggle-twin", "Punjab National Bank", "Zaggle", "PNB Zaggle Twin Credit Card",
     "https://www.zaggle.in/knowledge-hub/news/zaggle-partners-with-pnb-to-launch-ecofriendly-cobranded-retail-credit-cards",
     499, 499, None, "Partner rewards and network benefits on eligible personal purchases",
     ["rewards", "upi", "travel"], "RuPay / JCB", False),
    ("federal-one", "Federal Bank", "OneCard", "Federal Bank One Credit Card",
     "https://www.federal.bank.in/onecard", 0, 0, None,
     "OneCard reward points and app-based card controls on eligible purchases",
     ["rewards", "forex", "shopping"], "Visa / RuPay", False),
    ("federal-scapia", "Federal Bank", "Scapia", "Federal Bank Scapia Credit Card",
     "https://www.federal.bank.in/scapia", 0, 0, None,
     "Scapia coins on eligible purchases and travel bookings",
     ["travel", "forex", "rewards"], "Visa", False),
    ("federal-paisabazaar-paisaback", "Federal Bank", "Paisabazaar", "Federal Paisabazaar Paisaback Credit Card",
     "https://www.federal.bank.in/paisabazaar-federal-cobranded-credit-card", 499, 499,
     "waived on ₹1.5 lakh eligible annual spend", "Cash Points on eligible grocery, retail, e-commerce and UPI purchases",
     ["cashback", "groceries", "upi"], "RuPay", False),
    ("indian-bank-one", "Indian Bank", "OneCard", "Indian Bank One Credit Card",
     "https://www.indianbank.in/wp-content/uploads/2019/03/Indian-Bank-launches-the-Indian-Bank-One-Co-Branded-Credit-Card-a-tech-enabled-credit-card-powered-by-Visa-and-RuPay.pdf",
     0, 0, None, "OneCard reward points and app-based controls on eligible purchases",
     ["rewards", "shopping", "online"], "Visa / RuPay", False),
    ("utkarsh-supermoney-supercard", "Utkarsh Small Finance Bank", "super.money", "Utkarsh super.money superCard",
     "https://www.utkarsh.bank.in/personal/cards/credit-card/supercard", 0, 0, None,
     "Cashback on eligible UPI and non-UPI purchases through super.money",
     ["upi", "cashback", "secured"], "RuPay", True),
]


def card(row):
    card_id, issuer, partner, name, url, joining, annual, waiver, reward, tags, network, secured = row
    annual_text = "No fee" if annual == 0 else f"₹{annual:,} + GST"
    if waiver:
        annual_text += f" ({waiver})"
    return {
        "id": card_id,
        "name": name,
        "issuer": issuer,
        "coBrandPartner": partner,
        "tagline": f"A {partner} co-branded card for eligible personal spending.",
        "network": network,
        "palette": ["#111827", "#374151"],
        "accent": "#fbbf24",
        "annualFee": annual_text,
        "annualFeeAmount": annual,
        "joiningFee": "No fee" if joining == 0 else f"₹{joining:,} + GST",
        "joiningFeeAmount": joining,
        "rewardLine": reward,
        "highlights": [
            reward + "; issuer and partner caps, exclusions and redemption rules apply.",
            "The regulated issuing bank, not the fintech partner, approves and issues this credit card.",
            (f"Renewal fee is {waiver}." if waiver else "Confirm current acquisition offers and fees before applying."),
        ],
        "bestFor": tags,
        "feeType": "free" if annual == 0 else "worth",
        "minSpend": "low" if annual <= 500 else "mid",
        "creditReq": "new" if secured else "good",
        "rating": 4.0,
        "ratingBasis": "Neutral cardIQ editorial baseline, not a customer or issuer rating.",
        "applyUrl": url,
        "sourceUrls": [url],
        "verifiedOn": "2026-10-11",
        "applicationsOpen": True,
        "availabilityNote": f"Available through {partner}, subject to {issuer} approval.",
        "secured": secured,
        "active": True,
        "termsNote": "Eligible transactions only; bank and partner exclusions, caps, redemption values and benefit conditions apply. Confirm current terms before applying.",
        "catalogBatch": BATCH,
    }


cards = json.loads(CATALOG.read_text())
existing = {item["id"] for item in cards}
new = [card(row) for row in PRODUCTS if row[0] not in existing]
cards.extend(new)
CATALOG.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n")
print(f"Added {len(new)} fintech co-branded cards; total {len(cards)}")
