#!/usr/bin/env python3
"""Add currently marketed personal cards from PNB, BOBCARD, IDBI and YES BANK."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "backend" / "cards_catalog.json"
VERIFIED = "2026-10-11"
BATCH = "expansion-pnb-bob-idbi-yes-34-2026-10-11"

# issuer, name, url, joining fee, annual fee, reward summary, tags, network,
# secured, restricted, optional annual-fee note
PRODUCTS = [
    # PNB's current KFS lists these seven consumer variants.
    ("Punjab National Bank", "PNB RuPay Platinum", "https://creditcard.pnb.bank.in/", 0, 500, "Reward points on eligible retail purchases", ["rewards", "shopping"], "RuPay", False, False, None),
    ("Punjab National Bank", "PNB RuPay Select", "https://creditcard.pnb.bank.in/", 500, 750, "Reward points and RuPay Select privileges on eligible purchases", ["rewards", "travel"], "RuPay", False, False, None),
    ("Punjab National Bank", "PNB RuPay Millennial", "https://creditcard.pnb.bank.in/", 399, 999, "Reward points and lifestyle benefits on eligible purchases", ["rewards", "shopping"], "RuPay", False, False, None),
    ("Punjab National Bank", "PNB Visa Classic", "https://creditcard.pnb.bank.in/", 0, 0, "Reward points on eligible everyday purchases", ["rewards"], "Visa", False, False, None),
    ("Punjab National Bank", "PNB Visa Gold", "https://creditcard.pnb.bank.in/", 0, 300, "Reward points on eligible everyday purchases", ["rewards", "shopping"], "Visa", False, False, None),
    ("Punjab National Bank", "PNB Visa Platinum", "https://creditcard.pnb.bank.in/", 0, 500, "Reward points and Platinum privileges on eligible purchases", ["rewards", "travel"], "Visa", False, False, None),
    ("Punjab National Bank", "PNB Visa Signature", "https://creditcard.pnb.bank.in/", 1500, 2000, "Premium rewards and travel privileges on eligible purchases", ["travel", "lounge", "rewards"], "Visa", False, False, None),

    # General consumer products shown in BOBCARD's live card selector.
    ("BOBCARD", "BOBCARD ETERNA", "https://www.bobcard.co.in/credit-card-types/eterna", 2499, 2499, "Accelerated rewards on eligible travel and dining spends", ["travel", "lounge", "rewards"], "Visa", False, False, None),
    ("BOBCARD", "BOBCARD Etihad Guest Premium", "https://www.bobcard.co.in/credit-card-types/bobcard-etihad-guest-premium", 4999, 4999, "Etihad Guest miles and premium travel benefits", ["travel", "airline", "lounge"], "Visa", False, False, None),
    ("BOBCARD", "BOBCARD Etihad Guest", "https://www.bobcard.co.in/credit-card-types/bobcard-etihad-guest", 2499, 2499, "Etihad Guest miles on eligible purchases", ["travel", "airline", "rewards"], "Visa", False, False, None),
    ("BOBCARD", "BOBCARD PREMIER", "https://www.bobcard.co.in/credit-card-types/premier", 1000, 1000, "Accelerated rewards on eligible travel, dining and international spends", ["travel", "dining", "rewards"], "Visa", False, False, None),
    ("BOBCARD", "BOBCARD TIARA", "https://www.bobcard.co.in/credit-card-types/tiara", 2499, 2499, "Accelerated rewards and lifestyle benefits for eligible cardholders", ["shopping", "travel", "lounge"], "Visa", False, True, None),
    ("BOBCARD", "BOBCARD Cashback", "https://www.bobcard.co.in/credit-card-types/bobcard-cashback", 499, 499, "Cashback on eligible online and other purchases", ["cashback", "online", "shopping"], "Visa", False, False, None),
    ("BOBCARD", "BOBCARD EASY", "https://www.bobcard.co.in/credit-card-types/easy", 500, 500, "Accelerated rewards on eligible department-store and entertainment spends", ["rewards", "shopping"], "Visa", False, False, None),
    ("BOBCARD", "BOBCARD SELECT", "https://www.bobcard.co.in/credit-card-types/select", 0, 750, "Accelerated rewards on eligible online shopping and dining", ["online", "dining", "rewards"], "Visa", False, False, "waived on ₹70,000 eligible annual spend"),
    ("BOBCARD", "Snapdeal BOBCARD", "https://www.bobcard.co.in/credit-card-types/snapdeal-bobcard", 249, 249, "Cashback on eligible Snapdeal purchases and rewards on other spends", ["cashback", "online", "shopping"], "Mastercard", False, False, None),
    ("BOBCARD", "HPCL ENERGIE BOBCARD", "https://www.bobcard.co.in/credit-card-types/hpcl-energie", 500, 500, "Fuel benefits and rewards on eligible HPCL purchases", ["fuel", "rewards"], "RuPay", False, False, None),
    ("BOBCARD", "IRCTC BOBCARD", "https://www.bobcard.co.in/credit-card-types/irctc", 500, 350, "Railway rewards and savings on eligible IRCTC bookings", ["travel", "rail", "rewards"], "RuPay", False, False, None),
    ("BOBCARD", "BOBCARD Scapia", "https://www.bobcard.co.in/credit-card-types/bobcard-scapia-credit-card", 0, 0, "Scapia coins on eligible purchases and travel bookings", ["travel", "forex", "rewards"], "Visa / RuPay", False, False, None),
    ("BOBCARD", "BOBCARD Uni GoldX", "https://www.bobcard.co.in/credit-card-types/bobcard-uni-goldx", 0, 0, "Uni Coins on eligible purchases", ["rewards", "forex", "shopping"], "Visa", False, False, None),
    ("BOBCARD", "BOBCARD One", "https://www.bobcard.co.in/credit-card-types/bobcard-one", 0, 0, "Reward points on eligible purchases with a low foreign-currency markup", ["rewards", "forex", "shopping"], "Visa", False, False, None),
    ("BOBCARD", "BOBCARD PRIME", "https://www.bobcard.co.in/credit-card-types/prime", 0, 0, "Reward points on eligible purchases against a fixed deposit", ["rewards", "secured"], "Visa", True, False, None),

    # IDBI's live overview and FAQ identify these four currently offered variants.
    ("IDBI Bank", "IDBI Bank Aspire Platinum", "https://www.idbibank.in/aspire-credit-card.aspx", 0, 0, "Delight Points on eligible everyday purchases", ["rewards", "shopping"], "Visa", False, False, None),
    ("IDBI Bank", "IDBI Bank Royale Signature", "https://www.idbibank.in/royale-signature-credit-card.aspx", 1499, 1499, "Accelerated Delight Points and travel privileges", ["travel", "rewards", "lounge"], "Visa", False, False, None),
    ("IDBI Bank", "IDBI Bank Euphoria World", "https://www.idbibank.in/Euphoria-credit-card.aspx", 0, 1499, "Accelerated Delight Points on eligible travel spends", ["travel", "lounge", "rewards"], "Mastercard", False, False, "waived on ₹1.5 lakh eligible annual spend"),
    ("IDBI Bank", "IDBI Bank Imperium Platinum", "https://www.idbibank.in/Imperium-credit-card.aspx", 499, 499, "Delight Points on eligible purchases against a fixed deposit", ["rewards", "secured"], "Visa", True, False, "waived on ₹75,000 eligible annual spend"),

    # Public personal variants in YES BANK's current credit-card KFS.
    ("YES BANK", "YES BANK MARQUEE", "https://www.yesbank.in/personal-banking/yes-individual/cards/credit-cards/marquee-credit-card", 4999, 4999, "Premium YES Rewardz and travel privileges", ["travel", "lounge", "rewards"], "Issuer-selected variant", False, False, None),
    ("YES BANK", "YES BANK RESERV", "https://www.yesbank.in/personal-banking/yes-individual/cards/credit-cards/reserv-credit-card", 2499, 2499, "Accelerated YES Rewardz on eligible online and offline purchases", ["travel", "lounge", "rewards"], "Issuer-selected variant", False, False, None),
    ("YES BANK", "YES BANK ELITE+", "https://www.yesbank.in/personal-banking/yes-individual/cards/credit-cards/elite-plus-credit-card", 999, 999, "Accelerated YES Rewardz on eligible online shopping", ["online", "travel", "rewards"], "Issuer-selected variant", False, False, None),
    ("YES BANK", "YES BANK SELECT", "https://www.yesbank.in/personal-banking/yes-individual/cards/credit-cards/select-credit-card", 499, 499, "YES Rewardz and lifestyle benefits on eligible purchases", ["rewards", "shopping"], "Issuer-selected variant", False, False, None),
    ("YES BANK", "YES BANK ACE", "https://www.yesbank.in/personal-banking/yes-individual/cards/credit-cards/ace-credit-card", 499, 499, "YES Rewardz on eligible everyday purchases", ["rewards", "shopping"], "Issuer-selected variant", False, False, None),
    ("YES BANK", "YES BANK Wellness", "https://www.yesbank.in/personal-banking/yes-individual/cards/credit-cards/wellness-credit-card", 1499, 1499, "Health and wellness benefits with rewards on eligible purchases", ["health", "rewards"], "Issuer-selected variant", False, False, None),
    ("YES BANK", "YES BANK Wellness Plus", "https://www.yesbank.in/personal-banking/yes-individual/cards/credit-cards/wellness-plus-credit-card", 1999, 1999, "Enhanced health, wellness and travel benefits", ["health", "travel", "lounge"], "Issuer-selected variant", False, False, None),
    ("YES BANK", "YES BANK RuPay Credit Card", "https://www.yesbank.in/personal-banking/yes-individual/cards/credit-cards/rupay-credit-card", 0, 0, "YES Rewardz on eligible card and UPI purchases", ["upi", "rewards"], "RuPay", False, False, None),
]


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def make_card(row):
    issuer, name, url, joining, annual, reward, tags, network, secured, restricted, waiver = row
    annual_text = "No fee" if annual == 0 else f"₹{annual:,} + GST"
    if waiver:
        annual_text += f" ({waiver})"
    joining_text = "No fee" if joining == 0 else f"₹{joining:,} + GST"
    premium = annual >= 1499
    card = {
        "id": f"{slug(issuer)}-{slug(name)}",
        "name": name,
        "issuer": issuer,
        "tagline": "For " + ("travel and premium privileges." if "travel" in tags else "eligible everyday rewards."),
        "network": network,
        "palette": ["#3f1d1d", "#8b1e2d"] if issuer == "Punjab National Bank" else (["#7c2d12", "#ea580c"] if issuer == "BOBCARD" else (["#1e3a8a", "#2563eb"] if issuer == "IDBI Bank" else ["#1e293b", "#334155"])),
        "accent": "#fbbf24",
        "annualFee": annual_text,
        "annualFeeAmount": annual,
        "joiningFee": joining_text,
        "joiningFeeAmount": joining,
        "rewardLine": reward,
        "highlights": [
            reward + "; issuer caps, exclusions and redemption rules apply.",
            (f"Annual membership fee is {waiver}." if waiver else "Confirm current acquisition offers and fee-waiver conditions with the issuer."),
            "Approval, card network and benefits remain subject to the issuer's current terms.",
        ],
        "bestFor": tags,
        "feeType": "free" if annual == 0 else ("premium" if premium else "worth"),
        "minSpend": "high" if premium else ("low" if annual <= 500 else "mid"),
        "creditReq": "new" if secured else ("excellent" if premium else "good"),
        "rating": 4.0,
        "ratingBasis": "Neutral cardIQ editorial baseline, not a customer or issuer rating.",
        "applyUrl": url,
        "sourceUrls": [url],
        "verifiedOn": VERIFIED,
        "applicationsOpen": True,
        "availabilityNote": f"Subject to {issuer} availability and approval.",
        "secured": secured,
        "active": True,
        "termsNote": "Eligible transactions only; issuer exclusions, caps, redemption values and benefit conditions apply. Confirm current terms before applying.",
        "catalogBatch": BATCH,
    }
    if restricted:
        card["recommendationEligible"] = False
        card["eligibilityNote"] = "Eligibility is limited to a specified customer segment and cannot be established by the general quiz."
    return card


cards = json.loads(CATALOG.read_text())
existing = {card["id"] for card in cards}
new = [make_card(row) for row in PRODUCTS if make_card(row)["id"] not in existing]
cards.extend(new)
CATALOG.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n")
print(f"Added {len(new)} cards from four issuers; total {len(cards)}")
