#!/usr/bin/env python3
"""Add the Kotak personal cards verified on the official issuer catalogue."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "backend" / "cards_catalog.json"
VERIFIED = "2026-10-17"
ISSUER = "Kotak Mahindra Bank"
RATING_BASIS = "Neutral cardIQ editorial baseline, not a customer or issuer rating."
TERMS = "Eligible transactions only; merchant classification, issuer exclusions, reward caps, redemption charges and benefit conditions apply. Check the linked issuer terms before applying."


def editorial(summary, ideal, strength, tradeoffs, verdict, alternatives):
    return {"summary": summary, "idealFor": ideal, "strengths": [strength], "tradeoffs": tradeoffs, "verdict": verdict, "alternatives": alternatives}


def alternative(card_id, name, reason):
    return {"id": card_id, "name": name, "reason": reason}


def card(card_id, name, page, fee, joining, reward, highlights, best_for, *, fee_type="worth", spend="mid", credit="good", network="Issuer-selected variant", secured=False, eligible=True, eligibility=None, reward_currency=None, lounge=None, forex=None, editorial_content):
    item = {
        "id": card_id, "name": name, "issuer": ISSUER, "tagline": reward, "network": network,
        "palette": ["#6b0f1a", "#b91c1c"], "accent": "#fde68a",
        "annualFee": fee[0], "annualFeeAmount": fee[1], "joiningFee": joining[0], "joiningFeeAmount": joining[1],
        "rewardLine": reward, "highlights": highlights, "bestFor": best_for, "feeType": fee_type,
        "minSpend": spend, "creditReq": credit, "rating": 4.0, "ratingBasis": RATING_BASIS,
        "applyUrl": page, "sourceUrls": [page], "verifiedOn": VERIFIED, "applicationsOpen": True,
        "availabilityNote": "Subject to Kotak Mahindra Bank availability, eligibility and approval.",
        "secured": secured, "active": True, "recommendationEligible": eligible, "catalogBatch": "kotak-official-2026-10-17",
        "termsNote": TERMS, "editorial": editorial_content,
    }
    if eligibility: item["eligibilityNote"] = eligibility
    if reward_currency: item["rewardCurrency"] = reward_currency
    if lounge: item["loungeBenefits"] = lounge
    if forex: item["forexMarkup"] = forex
    return item


INDIGO = "https://www.kotak.bank.in/en/personal-banking/cards/credit-cards/indigo-credit-card.html"
CARDS = [
    card("kotak-indigo-credit-card", "IndiGo Kotak Credit Card", INDIGO,
        ("₹1,500 + GST", 1500), ("₹1,500 + GST", 1500),
        "Up to 19 IndiGo BluChips per ₹100 on IndiGo bookings; 2 on dining and entertainment; 1 on other eligible spends",
        ["Welcome voucher of 2,500 IndiGo BluChips.", "Spend milestones can provide vouchers worth up to 7,500 IndiGo BluChips.", "Welcome, milestone and renewal vouchers expire six months after issue; reward exclusions apply."],
        ["travel", "flights", "dining", "rewards"], reward_currency="IndiGo BluChips",
        editorial_content=editorial("A mid-fee airline card for regular IndiGo flyers who can use BluChips and milestone vouchers before they expire.", ["Regular IndiGo flyers.", "People comfortable redeeming rewards inside the IndiGo programme."], "Up to 19 IndiGo BluChips per ₹100 on eligible IndiGo bookings.", ["The ₹1,500 annual fee has no published spend waiver.", "Bonus vouchers have six-month validity and value is concentrated in IndiGo."], "Shortlist it when IndiGo is already your normal airline; occasional flyers should compare a flexible travel-rewards card.", [alternative("kotak-kotak-air-plus-credit-card", "Kotak Air+", "Compare for travel value that is not tied to one airline."), alternative("idfc-indigo-credit-card", "IDFC FIRST IndiGo Credit Card", "Compare another IndiGo-linked earning structure and fee.")])) ,
    card("kotak-indigo-premium-credit-card", "IndiGo Kotak Premium Credit Card", INDIGO,
        ("₹3,000 + GST", 3000), ("₹3,000 + GST", 3000),
        "Up to 21 IndiGo BluChips per ₹100 on IndiGo bookings with premium welcome, milestone and lounge benefits",
        ["Welcome benefit includes 4,000 IndiGo BluChips and a 6E Eats voucher.", "Spend milestones can provide vouchers worth up to 16,000 IndiGo BluChips.", "The premium variant adds airport-lounge benefits; issuer conditions and reward exclusions apply."],
        ["travel", "flights", "lounge", "rewards"], spend="high", reward_currency="IndiGo BluChips",
        editorial_content=editorial("The premium IndiGo option raises the fee and concentrates more value in BluChips, milestones and travel privileges.", ["Frequent IndiGo flyers able to reach the published milestones.", "Travellers who will use the included lounge benefit."], "Up to 21 IndiGo BluChips per ₹100 on eligible IndiGo bookings.", ["The ₹3,000 annual fee requires consistent IndiGo use.", "Reward value and bonus-voucher validity remain tied to the IndiGo programme."], "Choose the premium variant only when the additional BluChips, milestones and lounge use clearly exceed the extra fee.", [alternative("kotak-indigo-credit-card", "IndiGo Kotak Credit Card", "Compare the lower-fee variant before paying for premium benefits."), alternative("kotak-kotak-air-plus-credit-card", "Kotak Air+", "Compare a less airline-specific travel currency.")])) ,
    card("kotak-white-reserve-credit-card", "Kotak White Reserve Credit Card", "https://www.kotak.bank.in/en/personal-banking/cards/credit-cards/white-reserve-credit-card.html",
        ("₹12,500 + GST (waived on ₹10 lakh eligible annual spend)", 12500), ("₹12,500 + GST", 12500),
        "White Pass milestone value, unlimited global lounge access and premium travel and lifestyle privileges",
        ["Unlimited global lounge access for primary and add-on cardholders, subject to programme terms.", "2% foreign-currency markup and two complimentary golf rounds each month at selected courses.", "Issuer value illustrations assume very high annual spending; actual value depends on benefit use."],
        ["premium", "travel", "lounge", "forex", "golf"], fee_type="premium", spend="vhigh", credit="excellent", lounge=["Unlimited global airport-lounge access for primary and eligible add-on cardholders, subject to issuer conditions."], forex="2% + applicable taxes",
        editorial_content=editorial("A high-fee metal card built for affluent customers who can use global lounges, milestone value and premium services repeatedly.", ["High-spending international travellers.", "Households that can use add-on lounge access and premium privileges."], "Unlimited global lounge access plus a 2% forex markup.", ["The ₹12,500 fee is substantial and the waiver requires ₹10 lakh of eligible annual spend.", "Kotak's headline value illustration assumes spending as high as ₹30 lakh a year."], "It can justify its fee for frequent premium travellers, but low or moderate spenders should not rely on the issuer's maximum-value illustration.", [alternative("hdfc-infinia-credit-card", "HDFC Bank INFINIA Metal Edition", "Compare premium travel redemption, lounge access and qualification requirements."), alternative("idfc-diamond-reserve-credit-card", "IDFC FIRST Diamond Reserve", "Compare another high-fee premium travel proposition.")])) ,
    card("kotak-upi-rupay-credit-card", "Kotak UPI RuPay Credit Card", "https://www.kotak.bank.in/en/personal-banking/cards/credit-cards/kotak-upi-rupay-credit-card.html",
        ("No annual fee", 0), ("No joining fee", 0), "3 Kotak Reward Points per ₹100 on eligible UPI and regular card transactions",
        ["Virtual-only RuPay credit card available to eligible existing Kotak credit-card customers.", "Cash redemption is ₹0.07 per point with a 2,000-point minimum; other catalogue redemptions may value points differently.", "No rewards on rent, fuel, railway, wallet, EMI, education, insurance, government or online gaming; utility rewards are capped by eligible spend."],
        ["upi", "lifetime-free", "rewards"], fee_type="free", spend="low", network="RuPay", eligible=False, eligibility="Available only to eligible existing Kotak credit-card customers.", reward_currency="Kotak Reward Points",
        editorial_content=editorial("A lifetime-free virtual companion card for existing Kotak cardholders who want to route eligible merchant UPI payments through credit.", ["Existing Kotak credit-card customers using merchant UPI.", "People who want a no-fee virtual RuPay companion card."], "No joining or annual fee and rewards on eligible UPI transactions.", ["It is not a standalone entry card: eligibility requires an existing Kotak credit card.", "The cash-equivalent reward rate is modest and many common categories are excluded."], "Useful as a free UPI companion, not as a reason by itself to start a Kotak credit-card relationship.", [alternative("indusind-platinum-rupay-credit-card", "IndusInd Bank Platinum RuPay", "Compare a RuPay option that may work as a primary card."), alternative("hdfc-hdfc-bank-upi-rupay-credit-card", "HDFC Bank UPI RuPay Credit Card", "Compare eligibility and UPI reward value.")])) ,
    card("kotak-white-credit-card", "Kotak White Credit Card", "https://www.kotak.bank.in/en/personal-banking/cards/credit-cards/white-credit-card.html",
        ("₹3,000 + GST (waived on ₹5 lakh eligible annual spend)", 3000), ("₹3,000 + GST", 3000),
        "White Pass milestone rewards with domestic and international airport-lounge access",
        ["Eight domestic lounge visits annually, limited to two per quarter, plus four international visits under issuer conditions.", "Introductory welcome voucher worth ₹1,500 on ₹30,000 spend within 60 days.", "Kotak's value illustration assumes ₹1 lakh monthly spend; actual value depends on milestone and lounge use."],
        ["premium", "travel", "lounge", "rewards"], spend="high", credit="excellent", lounge=["Up to eight domestic visits a year and four international visits, subject to quarterly and programme conditions."],
        editorial_content=editorial("A milestone-led premium card for customers who can use airport lounges and sustain the spending required for White Pass value.", ["Frequent domestic travellers with some international lounge use.", "Customers spending enough to reach White Pass milestones and the fee waiver."], "A mix of domestic and international lounge visits at a mid-premium fee.", ["The ₹5 lakh fee-waiver threshold is much higher than many mid-fee cards.", "The issuer's maximum value illustration assumes ₹12 lakh annual spending."], "Consider it for lounge and milestone use, but calculate value using your own spending rather than the issuer's illustration.", [alternative("kotak-white-reserve-credit-card", "Kotak White Reserve Credit Card", "Compare only if unlimited lounge access and premium services justify a much higher fee."), alternative("idfc-metal-credit-card-ashva", "IDFC FIRST Ashva", "Compare a different mid-premium travel and reward structure.")])) ,
    card("kotak-zen-credit-card", "Kotak Zen Credit Card", "https://www.kotak.bank.in/en/personal-banking/cards/credit-cards/zen-signature-credit-card/features.html",
        ("₹1,500 + GST (waived on ₹1.5 lakh eligible annual spend)", 1500), ("₹1,500 + GST", 1500),
        "10 Zen Points per ₹150 on eligible shopping and 5 per ₹150 on other eligible purchases",
        ["Milestones award 7,500 points at ₹3 lakh annual spend and another 7,500 at ₹6 lakh.", "Includes domestic and international lounge visits subject to issuer programme conditions.", "Cash redemption is ₹0.20 per Zen Point with a minimum redemption threshold; exclusions apply."],
        ["shopping", "rewards", "lounge", "travel"], reward_currency="Zen Points",
        editorial_content=editorial("A shopping-and-milestone card whose fee is relatively easy to waive, with lounge access adding value for occasional travellers.", ["Shoppers who can spend at least ₹1.5 lakh a year to waive the fee.", "Customers likely to reach the ₹3 lakh or ₹6 lakh milestones."], "Accelerated shopping rewards plus milestone points and lounge access.", ["Cash redemption reduces each Zen Point to ₹0.20.", "The strongest value requires reaching annual milestones, not just ordinary spending."], "A credible mid-fee option when shopping and milestone spend align; otherwise compare simpler cashback cards.", [alternative("kotak-kotak-cashback-plus-credit-card", "Kotak Cashback+", "Compare simpler cashback with a lower annual fee."), alternative("hdfc-millennia-credit-card", "HDFC Bank Millennia", "Compare online-shopping rewards and fee-waiver requirements.")])) ,
    card("kotak-811-dream-different-credit-card", "Kotak 811 Dream Different Credit Card", "https://www.kotak.bank.in/en/personal-banking/cards/credit-cards/811-dream-different-credit-card/milestone-program.html",
        ("No annual fee", 0), ("No joining fee", 0), "2 reward points per ₹100 online and 1 per ₹100 on other eligible purchases",
        ["Credit limit can be up to 90% of the supporting Kotak term deposit.", "Interest-free cash withdrawal can extend up to 48 days, but a processing fee applies to each withdrawal.", "Fuel and railway surcharge waivers are capped; reward exclusions and secured-card conditions apply."],
        ["secured", "credit-building", "lifetime-free", "online"], fee_type="free", spend="low", credit="new", network="Visa Platinum", secured=True, eligibility="Issued against an eligible Kotak term deposit; the bank determines the final credit limit and approval.", reward_currency="Kotak Reward Points",
        editorial_content=editorial("A lifetime-free FD-backed card for building or rebuilding credit while retaining basic online rewards and cash-access features.", ["People without sufficient unsecured-card eligibility.", "Kotak customers comfortable placing a term deposit as security."], "No joining or annual fee, with a credit limit linked to the supporting deposit.", ["The fixed deposit remains committed as security for the card.", "Reward value is secondary and cash withdrawal still carries a processing charge."], "A practical credit-building route when the deposit requirement is acceptable; compare deposit terms before focusing on rewards.", [alternative("idfc-wow", "IDFC FIRST WOW!", "Compare another lifetime-free FD-backed card and its forex proposition."), alternative("idfc-secured-rupay-credit-card", "IDFC FIRST EA₹N", "Compare another secured route with RuPay support.")])) ,
]


def main():
    cards = json.loads(CATALOG.read_text())
    by_id = {item["id"]: item for item in CARDS}
    retained = [item for item in cards if item["id"] not in by_id]
    retained.extend(CARDS)
    CATALOG.write_text(json.dumps(retained, ensure_ascii=False, indent=2) + "\n")
    print(f"Added or refreshed {len(CARDS)} Kotak cards; catalogue now has {len(retained)} cards")


if __name__ == "__main__":
    main()
