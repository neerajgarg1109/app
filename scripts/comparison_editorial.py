"""Three source-reviewed comparisons with bounded, reproducible examples."""
from decimal import Decimal
from html import escape

CHECKED = '2026-10-29'
FLIPKART = 'axis-flipkart-axisbank-credit-card-vs-sbi-flipkart-sbi-card'
NEU = 'hdfc-tata-neu-plus-vs-sbi-tata-neu-plus-sbi-card'
FOOD = 'axis-axis-bank-ace-credit-card-vs-hdfc-swiggy-ornge-hdfc-bank-credit-card'


def earn(spend, rate, cap=None):
    value = Decimal(str(spend)) * Decimal(str(rate))
    return min(value, Decimal(str(cap))) if cap is not None else value


def examples(slug):
    if slug == FLIPKART:
        normal = earn(10000, '.05') + earn(2000, '.075') + earn(5000, '.01')
        return [('One month: ₹10,000 Flipkart + ₹2,000 Myntra + ₹5,000 other eligible purchases', normal, normal),
                ('One quarter: ₹90,000 on Flipkart, with no other purchases', earn(90000, '.05', 4000), earn(90000, '.05', 4000)),
                ('One quarter: ₹1,50,000 at merchants qualifying for the 4% tier on both cards', earn(150000, '.04'), earn(150000, '.04', 4000))]
    if slug == NEU:
        return [('₹20,000 eligible merchant UPI using Tata Neu UPI ID', earn(20000, '.01', 500), earn(20000, '.01', 500)),
                ('₹20,000 eligible merchant UPI using another UPI ID', earn(20000, '.0025', 500), earn(20000, '.01', 500)),
                ('₹80,000 eligible merchant UPI using Tata Neu UPI ID', earn(80000, '.01', 500), earn(80000, '.01', 500))]
    if slug == FOOD:
        return [('One statement: ₹4,000 qualifying Swiggy purchases + ₹10,000 eligible offline purchases', earn(4000, '.04', 500) + earn(10000, '.015'), earn(4000, '.05', 1500) + earn(10000, '.01', 1000)),
                ('One statement: ₹20,000 qualifying Swiggy + ₹10,000 online purchases earning ACE base rate and Ornge accelerated rate', earn(20000, '.04', 500) + earn(10000, '.015'), earn(30000, '.05', 1500)),
                ('One statement: ₹40,000 other eligible offline purchases', earn(40000, '.015'), earn(40000, '.01', 1000))]
    return []


REVIEWS = {
    FLIPKART: {
        'summary': 'These cards have similar shopping headline rates. The useful differences are merchant eligibility, the preferred-merchant cap and the fee offer actually available to you—not the Flipkart name alone.',
        'left': 'Choose Axis when the merchants you use qualify for its preferred tier and its uncapped 4% earn is useful. Its published nil joining fee is a limited-period offer, not permanent free ownership.',
        'right': 'Choose SBI when its merchant list and acquisition terms fit better. Its separate quarterly caps include the 4% merchant tier; do not project that tier as unlimited.',
        'rules': 'Both provide 5% on eligible Flipkart/Cleartrip and 7.5% on Myntra, with separate ₹4,000 quarterly caps for those partners. Axis lists unlimited preferred-merchant 4%; SBI caps that tier at ₹4,000 per quarter. Both exclude categories including fuel, rent, wallets, insurance and EMI purchases. Merchant lists and quarter definitions must be checked separately.',
        'caveat': 'The first example assumes unused caps. The quarter examples use one applicable issuer reward quarter and no earlier qualifying spend. The ₹1,50,000 example is a cap illustration, not a spending recommendation; it assumes eligible merchants on BOTH programmes, whose lists can differ. Fees, taxes, refunds and transaction-level rounding are excluded. Neither card has a reward advantage in every shopping basket.',
        'sources': [('Axis cashback terms', 'https://www.axis.bank.in/docs/default-source/default-document-library/cashback-tncs---final.pdf?sfvrsn=b55a0e1a_5'), ('SBI reward booklet', 'https://www.sbicard.com/sbi-card-en/assets/docs/pdf/personal/cards/Flipkart-SBI-CreditCard-TandC-Booklet.pdf'), ('Axis fees and current joining offer', 'https://www.axis.bank.in/cards/credit-card/flipkart-axisbank-credit-card'), ('SBI product and fees', 'https://www.sbicard.com/en/personal/credit-cards/flipkart-sbi-card.html')],
        'unit': 'cashback',
    },
    NEU: {
        'summary': 'For eligible merchant UPI, your payment app can change the HDFC result. Compare the exact RuPay variant and the reward period before choosing between two cards with similar Tata-brand positioning.',
        'left': 'Choose HDFC when you are comfortable using Tata Neu UPI ID for the full eligible UPI rate and its voucher-based lounge process suits you. Other UPI IDs earn a lower base rate under the checked terms.',
        'right': 'Choose SBI when you want its published 1% eligible RuPay UPI earn without the HDFC-specific Tata Neu UPI-ID bonus condition. The statement-cycle cap still limits the return.',
        'rules': 'HDFC pays 0.25% on eligible UPI plus 0.75% through Tata Neu UPI ID, with 500 NeuCoins per calendar-month UPI cap. SBI lists 1% on eligible RuPay UPI with 500 NeuCoins per statement-cycle cap. NeuCoins are for eligible Tata redemptions; ₹1 redemption value does not make them withdrawable bank cash. Extra NeuPass promotions are separate.',
        'caveat': 'Examples assume the entire spend falls inside one eligible reward period, with no previous UPI rewards, refunds or excluded merchants. HDFC calendar months and SBI statement cycles need not align. All outputs are NeuCoins, not cash. Joining fees, renewal fees, paid plans and separate NeuPass bonuses are excluded. Verify network and app support before applying.',
        'sources': [('HDFC UPI rates, caps and fee schedule', 'https://www.hdfc.bank.in/credit-cards/tata-neu-plus-hdfc-bank-credit-card'), ('SBI NeuCoin and UPI terms, section 11.3', 'https://www.sbicard.com/sbi-card-en/assets/docs/pdf/ekit-tncs/Tata-Neu-Plus-Booklet.pdf'), ('SBI product terms', 'https://www.sbicard.com/en/personal/credit-cards/tata-neu-plus-sbi-card.html')],
        'unit': 'NeuCoins',
    },
    FOOD: {
        'summary': 'ACE combines eligible Android Google Pay bills with food-delivery rewards. Swiggy Ornge focuses on qualifying Swiggy and selected online purchases. The shared caps and minimum transaction amounts matter more than comparing 4% with 5% in isolation.',
        'left': 'Choose ACE when eligible Google Pay bills or ordinary purchases are a larger part of your spending. Its 5% bills and 4% partner tiers share a ₹500 statement cap; other eligible purchases earn 1.5%. The Google Pay bill benefit requires Android.',
        'right': 'Choose Ornge when eligible Swiggy and listed online purchases dominate. Their 5% tier shares a ₹1,500 billing-cycle cap; its 1% other tier is capped at ₹1,000. The checked terms require at least ₹249 per 5% transaction and ₹100 per 1% transaction.',
        'rules': 'Swiggy Ornge is distinct from Swiggy BLCK and the older Swiggy HDFC card. Use its own 15 October 2026 terms. Eligible online merchant/MCC lists determine the 5% rate. ACE and Ornge have different excluded categories; neither headline rate applies to every payment. Compare renewal-waiver spending separately from reward eligibility.',
        'caveat': 'Examples use one statement period, unused caps and transactions meeting both issuers’ minimums and category rules. The online purchases in row two must qualify for Ornge’s 5% while earning only ACE’s 1.5% base rate. No Google Pay bill spend is included in these paired examples. Figures are gross cashback before membership fees, taxes, reversals and transaction rounding; welcome memberships are not assigned a cash value.',
        'sources': [('Axis ACE reward rates, combined cap and Android condition', 'https://www.axis.bank.in/docs/default-source/default-document-library/axis-bank-ace-credit-card-tncs.pdf?sfvrsn=a3effc42_6'), ('HDFC Ornge terms published 15 October 2026', 'https://www.hdfc.bank.in/content/dam/hdfcbankpws/in/en/personal-banking/discover-products/cards/credit-cards/swiggy-ornge-hdfc-bank-credit-card/pdf/tncs-swiggy-ornge-hdfc-bank-credit-card-15102026.pdf'), ('HDFC Ornge fees and availability', 'https://www.hdfc.bank.in/credit-cards/swiggy-ornge-hdfc-bank-credit-card')],
        'unit': 'cashback',
    },
}


def render_comparison(slug, left, right):
    review = REVIEWS.get(slug)
    if not review:
        return ''
    def amount(value):
        return f'{value:,.0f} NeuCoins' if review['unit'] == 'NeuCoins' else f'₹{value:,.0f}'
    rows = ''.join(f'<tr><th scope="row">{escape(label)}</th><td>{amount(a)}</td><td>{amount(b)}</td></tr>' for label, a, b in examples(slug))
    sources = ''.join(f'<li><a href="{escape(url, quote=True)}">{escape(label)}</a></li>' for label, url in review['sources'])
    return f'''<section aria-labelledby="detailed-decision"><h2 id="detailed-decision">Which card fits which spending pattern?</h2><p>{escape(review['summary'])}</p>
<h3>When to choose {escape(left['name'])}</h3><p>{escape(review['left'])}</p>
<h3>When to choose {escape(right['name'])}</h3><p>{escape(review['right'])}</p>
<h3>The limits that change the answer</h3><p>{escape(review['rules'])}</p>
<h2>Worked spending examples</h2><p>Illustrative eligible spending, calculated from the linked issuer rules. These are examples, not personalised return estimates.</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Worked spending examples"><table><caption>Gross {escape(review['unit'])} before fees and taxes</caption><thead><tr><th scope="col">Spending assumption</th><th scope="col">{escape(left['name'])}</th><th scope="col">{escape(right['name'])}</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>{escape(review['caveat'])}</p><h2>Sources for this comparison</h2><p class="muted">Comparison terms reviewed <time datetime="{CHECKED}">{CHECKED}</time>. Card summaries retain their own verification dates. Product terms can change.</p><ul>{sources}</ul></section>'''
