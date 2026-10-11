#!/usr/bin/env python3
"""Append the active HDFC personal-card batch verified on 11 October 2026."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "backend" / "cards_catalog.json"
BASE = "https://www.hdfc.bank.in/credit-cards/"

# slug, name, fee, waiver, reward summary, best-for, fee tier, spend tier, restricted
PRODUCTS = [
    ("millennia-credit-card", "HDFC Bank Millennia", 1000, "₹1 lakh", "5% CashBack Points on eligible partner merchants and 1% on other eligible spends", ["cashback", "shopping", "online"], "worth", "mid", False),
    ("moneyback-plus-credit-card", "HDFC Bank MoneyBack+", 500, "₹50,000", "Accelerated CashPoints on eligible partner and category spends", ["rewards", "shopping", "online"], "worth", "low", False),
    ("freedom-credit-card", "HDFC Bank Freedom", 500, "₹50,000", "Accelerated CashPoints on selected merchants and eligible everyday spending", ["rewards", "shopping"], "worth", "low", False),
    ("phonepe-hdfc-bank-uno-credit-card", "PhonePe HDFC Bank Uno", 499, "₹1 lakh", "Reward Points on eligible PhonePe, UPI, utility, travel and online purchases", ["rewards", "bills", "online"], "worth", "mid", False),
    ("phonepe-hdfc-bank-ultimo-credit-card", "PhonePe HDFC Bank Ultimo", 999, "₹2 lakh", "Enhanced Reward Points on eligible PhonePe, UPI, utility, travel and online purchases", ["rewards", "travel", "online"], "worth", "mid", False),
    ("infinia-credit-card", "HDFC Bank INFINIA Metal Edition", 12500, "₹10 lakh", "Premium Reward Points and SmartBuy benefits on eligible purchases", ["travel", "lounge", "rewards"], "premium", "vhigh", True),
    ("diners-club-black-metal-edition-credit-card", "HDFC Bank Diners Club Black Metal Edition", 10000, "₹8 lakh", "Premium Reward Points and accelerated SmartBuy rewards on eligible purchases", ["travel", "lounge", "rewards"], "premium", "vhigh", False),
    ("pixel-play-credit-card", "HDFC Bank PIXEL Play", 500, "₹1 lakh", "Customisable cashback on selected eligible categories and merchants", ["cashback", "shopping", "online"], "worth", "mid", False),
    ("pixel-go-credit-card", "HDFC Bank PIXEL Go", 250, "₹50,000", "Cashback on eligible everyday purchases through the PIXEL programme", ["cashback", "online"], "worth", "low", False),
    ("hdfc-bank-upi-rupay-credit-card", "HDFC Bank UPI RuPay Credit Card", 99, "₹25,000", "CashPoints on eligible UPI and other card purchases", ["rewards", "upi"], "worth", "low", True),
    ("regalia-gold-credit-card", "HDFC Bank Regalia Gold", 2500, "₹4 lakh", "Reward Points, milestone vouchers and travel privileges on eligible spends", ["travel", "lounge", "rewards"], "premium", "high", False),
    ("diners-privilege-credit-card", "HDFC Bank Diners Club Privilege", 1000, "₹3 lakh", "Reward Points and dining, entertainment and travel benefits", ["dining", "travel", "rewards"], "worth", "high", False),
    ("swiggy-hdfc-bank-credit-card", "Swiggy HDFC Bank Credit Card", 500, "₹2 lakh", "Cashback on eligible Swiggy, online and everyday purchases", ["cashback", "dining", "online"], "worth", "mid", False),
    ("swiggy-ornge-hdfc-bank-credit-card", "Swiggy Ornge HDFC Bank Credit Card", 500, "₹1.5 lakh", "Cashback and Swiggy membership benefits on eligible purchases", ["cashback", "dining", "online"], "worth", "mid", False),
    ("swiggy-blck-hdfc-bank-credit-card", "Swiggy BLCK HDFC Bank Credit Card", 1000, "₹2 lakh", "Enhanced cashback and Swiggy BLCK membership benefits on eligible purchases", ["cashback", "dining", "online"], "worth", "high", False),
    ("marriott-bonvoy-credit-card", "Marriott Bonvoy HDFC Bank Credit Card", 3000, None, "Marriott Bonvoy Points and hotel benefits on eligible purchases", ["travel", "hotels", "rewards"], "premium", "high", False),
    ("indianoil-hdfc-bank-credit-card", "IndianOil HDFC Bank Credit Card", 500, None, "Fuel Points on eligible IndianOil, grocery and bill-payment spends", ["fuel", "bills", "rewards"], "worth", "mid", False),
    ("irctc-credit-card", "IRCTC HDFC Bank Credit Card", 500, "₹1.5 lakh", "Reward Points for eligible railway bookings and everyday purchases", ["travel", "rail", "rewards"], "worth", "mid", False),
]


def record(product):
    slug, name, fee, waiver, reward, best_for, fee_type, spend, restricted = product
    url = BASE + slug
    fee_text = f"₹{fee:,} + GST" + (f" (waived on {waiver} eligible annual spend)" if waiver else "")
    card = {
        "id": "hdfc-" + slug,
        "name": name,
        "issuer": "HDFC Bank",
        "tagline": "For " + ("travel privileges and rewards." if "travel" in best_for else "eligible everyday rewards."),
        "network": "Issuer-selected variant",
        "palette": ["#7f1d1d", "#b91c1c"],
        "accent": "#fbbf24",
        "annualFee": fee_text,
        "annualFeeAmount": fee,
        "joiningFee": f"₹{fee:,} + GST",
        "joiningFeeAmount": fee,
        "rewardLine": reward,
        "highlights": [
            reward + "; issuer caps, exclusions and redemption rules apply.",
            (f"Renewal fee reversal requires {waiver} of qualifying annual spend." if waiver else "No spend-based fee waiver is represented; confirm the current fee terms with HDFC Bank."),
            "Benefits and eligibility remain subject to the current HDFC Bank product terms.",
        ],
        "bestFor": best_for,
        "feeType": fee_type,
        "minSpend": spend,
        "creditReq": "excellent" if fee_type == "premium" else "good",
        "rating": 4.0,
        "ratingBasis": "Neutral cardIQ editorial baseline, not a customer or issuer rating.",
        "applyUrl": url,
        "sourceUrls": [url],
        "verifiedOn": "2026-10-11",
        "applicationsOpen": True,
        "availabilityNote": "Subject to HDFC Bank availability and approval.",
        "secured": False,
        "active": True,
        "termsNote": "Eligible transactions only; HDFC Bank exclusions, caps, redemption values and benefit conditions apply. Confirm current terms before applying.",
        "catalogBatch": "expansion-hdfc-18-2026-10-11",
    }
    if restricted:
        card["recommendationEligible"] = False
        card["eligibilityNote"] = "Invitation or existing-card eligibility cannot be established by the general quiz."
    return card


cards = json.loads(CATALOG.read_text())
existing = {card["id"] for card in cards}
new = [record(product) for product in PRODUCTS if "hdfc-" + product[0] not in existing]
cards.extend(new)
CATALOG.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n")
print(f"Added {len(new)} HDFC personal cards; total {len(cards)}")
