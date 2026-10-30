"""Decision-focused content and crawlable research paths for public pages."""
from html import escape
from financial_copy import fee_copy
from urllib.parse import quote

CSS = '.card-facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:0}.card-facts dt{font-weight:700}.card-facts dd{margin:4px 0 0;overflow-wrap:anywhere}.product-image{display:block;width:240px;max-width:100%;height:180px;object-fit:contain;margin:16px auto}.research-links{display:flex;flex-wrap:wrap;gap:8px 20px}.table-scroll{overflow-x:auto}.table-scroll table{min-width:540px}table{border-collapse:collapse;width:100%}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #e4e2f1;padding:12px}'

TOPICS = {
    'cashback': ('best-cashback-credit-cards-india', 'Choosing a cashback card', [
        ('Where do you actually spend?', 'Separate purchases that qualify for accelerated cashback from excluded bills and other purchases. A headline rate is useful only for spending that earns it.'),
        ('Will you hit a cap?', 'Compare a normal month with a large-purchase month. Read whether the limit applies separately to online and offline purchases, to each merchant, or to the entire statement.'),
        ('How is the reward paid?', 'Check whether rewards become statement credit, partner balance or points. Do not treat a restricted redemption currency as cash in your bank account.')],
        'Hypothetical example: ₹10,000 of eligible monthly purchases at 2% produces ₹200 before caps. If the monthly cap were ₹150, the usable reward would be ₹150. These are illustrative inputs, not an offer from a listed card.'),
    'lifetime-free': ('best-lifetime-free-credit-cards-india', 'Checking a lifetime-free offer', [
        ('Is the waiver permanent?', 'Distinguish nil standard membership fees from a first-year promotion or a renewal fee waived after spending. Confirm the fee plan shown in your own application.'),
        ('Does the format change the fee?', 'Virtual, physical and companion versions can have different charges. Read both the joining and renewal fee fields instead of relying on a free label.'),
        ('Which other charges remain?', 'No membership fee does not describe every possible charge. Review the issuer schedule for borrowing, cash withdrawals, foreign-currency transactions and reward redemption.')],
        'Comparison exercise: write down the joining fee, renewal fee, any spend condition and the exact card variant for each option. If avoiding membership fees is your priority, remove conditional offers before comparing rewards.'),
    'travel': ('best-travel-credit-cards-india', 'Choosing rewards you can use on a trip', [
        ('Where can you redeem?', 'Compare airline-specific miles, hotel points and flexible travel rewards against routes and hotels you normally book. A larger points balance need not mean a cheaper trip.'),
        ('What does lounge access require?', 'Check the eligible programme, spending qualification, visit limits, guest rules and add-on terms. A membership and a complimentary visit are different benefits.'),
        ('What costs come with international use?', 'Read the issuer forex markup and the network conversion terms separately. Decide whether you can use the travel privileges often enough to justify the membership fee.')],
        'Comparison exercise: choose one trip you are likely to take. Check whether each reward currency can book it, what redemption restrictions apply and which benefits you would actually use. Exclude advertised perks you would not otherwise buy.'),
    'fuel': ('best-fuel-credit-cards-india', 'Comparing fuel rewards at your usual outlet', [
        ('Which petrol stations qualify?', 'Start with your normal fuel brand and payment method. Verify whether accelerated rewards apply to that outlet and how the issuer identifies eligible fuel transactions.'),
        ('Are rewards and surcharge relief separate?', 'Read the transaction-size limits and monthly ceilings for each benefit. A surcharge waiver is not the same thing as reward points credited on the purchase.'),
        ('Can you use the redemption?', 'Check point value and the eligible redemption channel before comparing headline reward percentages. Include the membership fee in your own annual calculation.')],
        'Comparison exercise: use a normal month’s fuel purchases, including the number and size of fills. Apply each eligible reward cap and surcharge-waiver limit separately, then compare the result after membership fees.'),
    'rupay-upi': ('best-rupay-upi-credit-cards-india', 'Checking a RuPay card for merchant UPI', [
        ('Is this exact card UPI-enabled?', 'Check the issuing bank, supported app and card variant. Do not infer that every network variant or every payment type has the same eligibility.'),
        ('Which purchases earn rewards?', 'Read the merchant-payment exclusions, minimum spends and reward caps for the UPI route. An online-card reward rate need not apply to scan-and-pay transactions.'),
        ('Is a paid plan part of the offer?', 'Separate the base card programme from optional app subscriptions, temporary merchant offers and paid reward tiers. Compare the costs of the version you would use.')],
        'Comparison exercise: list your regular merchant UPI payments, then remove any categories excluded by the card. Apply the base reward rules before considering an optional paid plan or a temporary offer.'),
    'beginner': ('best-first-credit-cards-india', 'Choosing a manageable first card', [
        ('Do you need a deposit-backed route?', 'Compare a secured card’s deposit commitment with its membership fees. Keep the deposit requirement separate from the fee: the money is security, not a reward.'),
        ('Are the rules understandable?', 'Choose a fee and reward structure you can track using normal purchases. Do not increase spending just to reach a fee waiver or welcome-benefit milestone.'),
        ('Can you confirm the access route?', 'Issuer approval remains separate from this shortlist. Check whether a product requires an existing account, an invitation, a partner app or a fixed deposit.')],
        'Comparison exercise: shortlist cards using spending you already expect, the amount you can set aside for a deposit if needed, and the membership fee you can justify. Leave out benefits whose conditions you do not expect to meet.'),
}


def shortlist_matches(card, category_id):
    """Use positive product attributes; a reward exclusion is not a benefit."""
    tags = set(card.get('bestFor') or [])
    if category_id == 'cashback':
        return 'cashback' in tags
    if category_id == 'fuel':
        return 'fuel' in tags
    if category_id == 'travel':
        return bool(tags & {'travel', 'flights'})
    if category_id == 'rupay-upi':
        return 'rupay' in card.get('network', '').lower() and 'upi' in tags
    if category_id == 'beginner':
        return card.get('secured') is True or card.get('creditReq') in {'new', 'fair'}
    if category_id == 'lifetime-free':
        fees = f'{card.get("annualFee", "")} {card.get("joiningFee", "")}'.lower()
        return (card.get('annualFeeAmount') == 0 and card.get('joiningFeeAmount') == 0
                and card.get('lifetimeFree') is not False
                and not any(word in fees for word in ('waiv', 'offer', 'first-year', 'first year', 'current', 'physical')))
    return True


def choosing_section(category_id):
    topic = TOPICS.get(category_id)
    if not topic:
        return ''
    _, title, questions, example = topic
    items = ''.join(f'<h3>{escape(q)}</h3><p>{escape(a)}</p>' for q, a in questions)
    return f'<section aria-label="Choosing criteria"><h2>{escape(title)}</h2>{items}<h3>A practical comparison</h3><p>{escape(example)}</p></section>'


def category_research(category_id, origin):
    topic = TOPICS.get(category_id)
    if not topic:
        return ''
    questions = ' '.join(q for q, _ in topic[2])
    return (f'<section><h2>Compare the details that affect your choice</h2><p>{escape(questions)} '
            'Use the product links below to compare published fees and conditions, then read the guide for a practical decision framework.</p>'
            f'<p><a href="{origin}/guides/{topic[0]}/">Read the {escape(topic[1].lower())} guide</a> · '
            f'<a href="{origin}/calculator/">Compare value using your own spending</a></p></section>')


def product_facts(card, origin, access):
    fields = [('Joining fee', fee_copy(card, 'joiningFee')),
              ('Annual / renewal fee', fee_copy(card)),
              ('Card network', card.get('network', 'Confirm with issuer')),
              ('Availability', (access or {}).get('accessExplanation') or card.get('availabilityNote') or 'Subject to issuer availability and approval.')]
    if card.get('secured'):
        fields.append(('Security requirement', 'Fixed deposit or other issuer-specified security required; check deposit and closure conditions.'))
    facts = ''.join(f'<div><dt>{escape(k)}</dt><dd>{escape(str(v))}</dd></div>' for k, v in fields)
    image = card.get('imageUrl')
    artwork = f'<img class="product-image" src="{escape(image, quote=True)}" alt="{escape(card["name"], quote=True)} official product artwork" width="240" height="180" decoding="async">' if image else ''
    return f'{artwork}<section class="card" aria-labelledby="fees-title"><h2 id="fees-title">Fees and application requirements</h2><dl class="card-facts">{facts}</dl><p class="muted">Read the complete fee wording: spend-based waivers and promotional offers have conditions. The issuer’s current application terms take precedence.</p></section>'


def product_research(card, categories, origin, issuer_slug):
    links = [f'<a href="{origin}/issuers/{issuer_slug}/">Compare {escape(card["issuer"])} credit cards</a>']
    for category in categories[:3]:
        label = category['label'] if category['label'].lower().endswith('credit cards') else category['label'] + ' credit cards'
        links.append(f'<a href="{origin}/categories/{quote(category["id"])}/">{escape(label)}</a>')
    links.append(f'<a href="{origin}/methodology/">How CardIQ researches and compares cards</a>')
    return '<section><h2>Continue your research</h2><div class="research-links">' + ''.join(links) + '</div></section>'
