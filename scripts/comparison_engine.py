"""Build-time comparison content; only the bounded spending scenario is interactive."""
import json
import hashlib
import re
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from pathlib import Path
from urllib.parse import urlencode

DATA = Path(__file__).with_name('data')
TOP_COMPARISONS = json.loads((DATA / 'top_comparisons.json').read_text())
PRIORITY = {row['slug']: row for row in TOP_COMPARISONS}
MITC = json.loads((DATA / 'comparison_mitc.json').read_text()) if (DATA / 'comparison_mitc.json').exists() else {}
YEAR = 2026
CATEGORIES = {'online': 'Online shopping', 'upi': 'UPI / QR', 'dining': 'Dining / groceries', 'travel': 'Travel / forex', 'utilities': 'Utilities'}
RULES = {
    'sbi-cashback-sbi': {'online': [.05, 2000], 'upi': [0, 0], 'utilities': [0, 0]},
    'hdfc-millennia-credit-card': {'online': [.05, 1000]},
    'icici-amazon-pay-credit-card': {'online': [.01, None]},
    'axis-flipkart-axisbank-credit-card': {'online': [.05, 4000, 3]},
    'hsbc-live-plus': {'dining': [.10, 1200]},
    'axis-airtel-axis-bank-credit-card': {'online': [.01, None], 'utilities': [.10, 0]},
    'hdfc-swiggy-hdfc-bank-credit-card': {'dining': [.10, 1500], 'online': [.05, 1500]},
    'hdfc-swiggy-ornge-hdfc-bank-credit-card': {'dining': [.05, 1500], 'online': [.05, 1500]},
}
ASSUMPTIONS = {
    'hdfc-millennia-credit-card': 'Online scenario means listed 5% merchants only. CashPoints valued at ₹1 for statement redemption; redemption fee, minimum balance and timing are excluded.',
    'icici-amazon-pay-credit-card': 'Online scenario means eligible non-Amazon purchases earning 1%. Rewards are Amazon Pay balance valued at ₹1 per unit, not bank cash. Prime/Amazon 5% is a different basket.',
    'axis-flipkart-axisbank-credit-card': 'Online scenario means eligible Flipkart/Cleartrip purchases only, not all online merchants; ₹4,000 quarterly cap is applied to three equal months.',
    'hsbc-live-plus': 'Dining/grocery scenario means eligible accelerated purchases only; ₹1,200 monthly shared cap. No other accelerated purchases are assumed.',
    'axis-airtel-axis-bank-credit-card': 'Utility scenario assumes no 1% base-category purchases, so the current base-linked utility cap is zero. Partner-wallet benefits are excluded; online means eligible base-category purchases.',
    'hdfc-swiggy-hdfc-bank-credit-card': 'Dining scenario means eligible Swiggy orders of at least ₹249 each, not all dining/groceries. Online means eligible 5% merchant categories. Check which original/Ornge/BLCK variant you are offered.',
    'hdfc-swiggy-ornge-hdfc-bank-credit-card': 'Dining scenario means eligible Swiggy orders of at least ₹249 each; online means eligible 5% categories. Both share one ₹1,500 cycle cap; this model uses one category only.',
    'sbi-cashback-sbi': 'Eligible online purchases only; ₹2,000 per statement online cap. UPI network and excluded utility categories do not earn cashback in this model.',
}
MODEL_SOURCES = {
    'sbi-cashback-sbi': ['https://www.sbicard.com/sbi-card-en/assets/docs/pdf/cashback-revised.pdf'],
    'hdfc-millennia-credit-card': ['https://www.hdfc.bank.in/content/dam/hdfcbankpws/in/en/personal-banking/discover-products/cards/credit-cards/millennia-credit-card/pdf/terms-and-conditions.pdf'],
    'axis-airtel-axis-bank-credit-card': ['https://www.axis.bank.in/docs/default-source/default-document-library/terms-and-conditions-for-airtel-cbcc-cvp.pdf'],
}


MODEL_FINGERPRINTS = json.loads((DATA / 'comparison_model_fingerprints.json').read_text())
MODEL_FIELDS = ['network','rewardLine','highlights','exclusions','rewardRedemption','annualFee','annualFeeAmount','joiningFee','joiningFeeAmount','verifiedOn']


def rules_for(card):
    signature = hashlib.sha256(json.dumps({k:card.get(k) for k in MODEL_FIELDS},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return RULES.get(card['id'], {}) if MODEL_FINGERPRINTS.get(card['id']) == signature else {}


def money(value):
    rounded = f'{Decimal(str(value)).quantize(Decimal(".01"), rounding=ROUND_HALF_UP):.2f}'
    whole, fraction = rounded.split('.')
    sign = '-' if whole.startswith('-') else ''
    whole = whole.lstrip('-')
    groups = [whole[-3:]]
    whole = whole[:-3]
    while whole:
        groups.insert(0, whole[-2:])
        whole = whole[:-2]
    return '₹' + sign + ','.join(groups) + '.' + fraction


def waiver(card):
    # Use the existing catalogue's sourced waiver parser, never guess from the fee tier.
    from cards_seed import card_economics_profile
    return card_economics_profile(card)['feeWaiverThreshold']


def short_name(card):
    aliases = {'sbi-cashback-sbi': 'SBI Cashback', 'hdfc-millennia-credit-card': 'HDFC Millennia', 'hdfc-tata-neu-infinity': 'Tata Neu Infinity', 'hdfc-tata-neu-plus': 'Tata Neu Plus', 'icici-amazon-pay-credit-card': 'Amazon Pay ICICI', 'axis-flipkart-axisbank-credit-card': 'Flipkart Axis'}
    name = aliases.get(card['id'], re.sub(r'\b(Credit Card|Bank Credit Card)\b', '', card['name']).strip())
    return name


def comparison_excerpt(left, right):
    """Use maintained issuer attributes, without inferring LTF from a zero fee alone."""
    facts = []
    for card in (left, right):
        fee = card.get('annualFeeAmount')
        fee_text = 'annual fee not verified' if fee is None else ('no annual fee' if fee == 0 else money(fee).removesuffix('.00') + ' annual fee before GST')
        if fee == 0 and 'lifetime' in str(card.get('annualFee', '')).lower():
            fee_text += ' (lifetime-free offer; check eligibility)'
        facts.append(f"{short_name(card)}: {fee_text}")
    # Keep a real pair-specific benefit, rather than a common editorial template.
    detail = next((str(c.get('forexMarkup')) for c in (left, right) if c.get('forexMarkup')), '')
    if detail:
        source = next(c for c in (left, right) if c.get('forexMarkup'))
        facts.append(f"{short_name(source)} forex: {detail}")
    elif left.get('rewardLine'):
        facts.append(f"{short_name(left)} rewards: {left['rewardLine']}")
    return '. '.join(facts).rstrip('.') + '.'


def generateComparisonSeoMeta(cardA, cardB, customOverride=None, origin='https://findmybest.cards'):
    priority = next((p for p in TOP_COMPARISONS if {p['cardA'], p['cardB']} == {cardA['id'], cardB['id']}), {})
    custom = {**priority, **(customOverride or {})}
    a, b = short_name(cardA), short_name(cardB)
    slug = custom.get('slug', f'{cardA["id"]}-vs-{cardB["id"]}')
    text = ' '.join(str(c.get(k, '')) for c in (cardA, cardB) for k in ('bestFor', 'network', 'rewardLine')).lower()
    if 'rupay' in text or 'upi' in text: suffix = 'RuPay: Best for UPI Scan & Pay Cashback?'
    elif cardA['issuer'] == cardB['issuer']: suffix = f'Which {cardA["issuer"]} Card Should You Apply For?'
    elif any(c.get('annualFeeAmount') == 0 for c in (cardA, cardB)) and any(c.get('annualFeeAmount', 0) > 0 for c in (cardA, cardB)):
        suffix = f'Is the ₹{max(c.get("annualFeeAmount", 0) for c in (cardA,cardB))} Fee Worth It in 2026?'
    elif any(t in text for t in ('travel', 'forex', 'miles')): suffix = 'Forex Markup, Lounge Rules & Winner'
    else: suffix = '(2026): Real ₹ Cashback & Capping Math'
    title = custom.get('title') or f'{a} vs {b}: {suffix}'
    if not custom.get('title') and len(title) >= 65:
        # Retain distinguishable product names before dropping the optional formula suffix.
        title = f'{a} vs {b}'
        if len(title) >= 65:
            a = a[:27].rstrip(); b = b[:27].rstrip(); title = f'{a} vs {b}'
    return {'title': title, 'metaDescription': f'Compare {a} and {b}: eligible rewards, fee waivers, exclusions and lounge conditions. See dated issuer sources and a spending scenario.', 'h1': custom.get('h1', f'{a} vs {b}: fees, rewards and conditions'), 'canonicalUrl': f'{origin.rstrip("/")}/compare/{slug}/', 'slug': slug}


def estimate(card, monthly=20000, category='online', year='renewal'):
    rule = rules_for(card).get(category)
    threshold = waiver(card)
    fee = card.get('joiningFeeAmount') if year == 'first' else card.get('annualFeeAmount')
    # A renewal waiver cannot be applied to a first-year joining fee.
    waived = year == 'renewal' and threshold is not None and monthly * 12 >= threshold
    charged = None if fee is None else Decimal(str(0 if waived else fee)) * Decimal('1.18')
    gross = None
    if rule:
        rate, cap, *period = rule
        months = period[0] if period else 1
        gross = Decimal(str(monthly)) * months * Decimal(str(rate))
        if cap is not None: gross = min(gross, Decimal(str(cap)))
        gross *= Decimal(12) / months
    return {'gross': float(gross) if gross is not None else None, 'fee': float(charged) if charged is not None else None, 'net': float(gross - charged) if gross is not None and charged is not None else None, 'waived': waived}


def go_link(card, pair, placement, origin):
    return f'{origin}/go/{card["id"]}/?{urlencode({"subid": placement, "pair": pair})}'


def cta(card, pair, placement, origin, label=None):
    if not card.get('active', True) or not card.get('applicationsOpen', True):
        return '<p>Applications are not confirmed open for this card. Check the issuer.</p>'
    return f'<a class="cta" href="{escape(go_link(card,pair,placement,origin), quote=True)}" rel="sponsored nofollow noopener" target="_blank">{escape(label or "Apply for " + short_name(card))} →</a>'


def artwork(card):
    if not card.get('imageUrl'): return '<p class="muted">Official artwork unavailable</p>'
    return f'<img class="product-image" src="{escape(card["imageUrl"],quote=True)}" alt="{escape(card["name"],quote=True)} card" width="240" height="180" decoding="async">'


def evidence(card):
    return ' '.join(str(v) for v in [card.get('rewardLine',''), *(card.get('highlights') or []), *(card.get('exclusions') or []), *(card.get('loungeBenefits') or []), card.get('forexMarkup',''), card.get('termsNote','')])


def known_text(card, terms, fallback='Not verified in the maintained record. Check the linked issuer terms.'):
    lines = [card.get('rewardLine',''), *(card.get('highlights') or []), *(card.get('exclusions') or []), *(card.get('loungeBenefits') or []), card.get('forexMarkup','')]
    found = list(dict.fromkeys(line for line in lines if line and any(re.search(r'\b' + re.escape(t), line.lower()) for t in terms)))
    return ' '.join(found) or fallback


def pdf_links(card):
    urls = list(dict.fromkeys([*(card.get('sourceUrls') or []), *MODEL_SOURCES.get(card['id'], [])]))
    issuer_mitc = MITC.get(card['issuer'], {})
    if issuer_mitc.get('url'): urls.insert(0, issuer_mitc['url'])
    pdfs = list(dict.fromkeys(u for u in urls if '.pdf' in u.lower()))
    if not pdfs: return 'Direct MITC PDF not verified. ' + f'<a href="{escape(card["applyUrl"],quote=True)}" rel="noopener" target="_blank">Official product page and terms</a>'
    return ' '.join(f'<a href="{escape(u,quote=True)}" rel="noopener" target="_blank">{"Issuer MITC PDF" if "mitc" in u.lower() else "Issuer benefit / terms PDF"}</a>' for u in pdfs)


def render_comparison_page(left, right, meta, cards, custom=None, extra=''):
    custom = custom or {}; pair = meta['slug']; origin = meta['canonicalUrl'].split('/compare/')[0]
    note = custom.get('note', 'Compare fees, caps and exclusions against your actual eligible spending. A higher headline rate is not a universal winner.')
    verdicts = custom.get('verdicts') or [
        [(c.get('editorial') or {}).get('idealFor', ['Your spending matches its documented eligible categories.'])[0],
         f'Its fee offer fits your budget: {c.get("annualFee", "check the issuer")}.',
         f'Renewal waiver: {money(waiver(c)) + " eligible annual spend" if waiver(c) is not None else "not verified; do not assume a waiver"}.'] for c in (left,right)]
    boxes = ''
    for index, card in enumerate((left,right)):
        facts = ''.join(f'<li>{escape(line)}</li>' for line in verdicts[index])
        boxes += f'<article class="card">{artwork(card)}<h3>Pick {escape(short_name(card))} if:</h3><ul>{facts}</ul><h4>CardIQ view</h4><p>{escape((card.get("editorial") or {}).get("summary",card.get("rewardLine","")))}</p>{cta(card,pair,"verdict_box_card_a" if index==0 else "verdict_box_card_b",origin)}</article>'
    mitc_dates = ', '.join(f'{short_name(c)}: {MITC.get(c["issuer"], {}).get("linkCheckedOn") or "retrieval not confirmed"}' for c in (left,right))
    dates = ', '.join(f'{short_name(c)}: {c.get("verifiedOn", "not verified")}' for c in (left,right))
    verdict = f'<section id="verdict" class="comparison-block"><h2>10-second CardIQ verdict</h2><h3>Key decision</h3><p>{escape(note)}</p><div class="grid">{boxes}</div><p class="muted">Issuer MITC link checked: {escape(mitc_dates)} | No Sponsored Ranking. Issuer record checked: {escape(dates)}. Link checks confirm document availability, not a complete re-audit of every product rule.</p><p>CardIQ may earn a commission from a live partner application link. Compensation does not determine this comparison.</p></section>'
    models=[]; outputs=''
    for c in (left,right):
        profile={'id':c['id'],'name':short_name(c),'rules':rules_for(c),'annualFee':c.get('annualFeeAmount'),'joiningFee':c.get('joiningFeeAmount'),'waiver':waiver(c),'apply':go_link(c,pair,'calculator_winner_cta',origin)};models.append(profile)
        result=estimate(c)
        assumption = ASSUMPTIONS.get(c['id'], 'Reward rates, caps or redemption value are not sufficiently structured for an exact rupee estimate. This is not a zero-reward claim.')
        if c['id'] in RULES and not rules_for(c): assumption = 'This card record changed after the calculator model was reviewed. Rewards are not estimated until its inputs are reviewed again.'
        values=lambda k: money(result[k]) if result[k] is not None else 'Not estimated'
        outputs+=f'<article class="card" data-result="{escape(c["id"])}"><h3>{escape(short_name(c))}</h3><dl><dt>Gross annual rewards (cash-equivalent)</dt><dd data-value="gross">{values("gross")}</dd><dt>Renewal fee + 18% GST</dt><dd data-value="fee">{values("fee")}</dd><dt>Net annual value</dt><dd data-value="net">{values("net")}</dd></dl><p>{escape(assumption)}</p></article>'
    payload=json.dumps(models,ensure_ascii=False).replace('<','\\u003c')
    calculator=f'''<section id="spending" class="comparison-block" data-comparison-calculator><h2>Real rupee net value slider</h2>
<p>Illustration: equal eligible spending in each of 12 months / statement cycles, no refunds and no prior cap usage. Different merchant baskets may apply to each card; read both assumptions. Rewards are cash-equivalent estimates, not profit or guaranteed savings.</p>
<label for="monthly-spend">Monthly spending: <output id="spend-output">₹20,000</output></label><input id="monthly-spend" type="range" min="10000" max="100000" step="1000" value="20000">
<label for="spend-category">Eligible purchase scenario</label><select id="spend-category">{''.join(f'<option value="{key}">{label}</option>' for key,label in CATEGORIES.items())}</select>
<label for="fee-year">Membership year</label><select id="fee-year"><option value="renewal">Renewal year (eligible spend may waive fee)</option><option value="first">First year (joining fee; renewal waiver not applied)</option></select>
<div class="grid">{outputs}</div><div id="calculator-winner" aria-live="polite">Compare the assumptions before choosing; unknown economics are not ranked.</div>
<p>Excludes borrowing interest, redemption charges, extra transaction fees, vouchers, welcome gifts, lounge valuations, FX conversion and paid plans. Selecting Travel / Forex does not assume every travel booking is an overseas transaction. Waiver-eligible spend can differ from reward-eligible spend: this simplified scenario assumes all entered spend counts toward the displayed renewal threshold. Confirm the issuer's exact threshold boundary.</p><noscript><p>The ₹20,000/month online scenario above is available without JavaScript. Enable JavaScript only to change the scenario.</p></noscript><script type="application/json" id="comparison-models">{payload}</script></section>'''
    rows=[('Joining fee + GST',lambda c:f'{c.get("joiningFee","Not verified")} · {money(c["joiningFeeAmount"]*1.18) + " incl. GST" if c.get("joiningFeeAmount") is not None else "amount not verified"}'),('Renewal fee + GST',lambda c:f'{c.get("annualFee","Not verified")} · {money(c["annualFeeAmount"]*1.18) + " incl. GST before waiver" if c.get("annualFeeAmount") is not None else "amount not verified"}'),('Annual spend for renewal waiver',lambda c:money(waiver(c)) if waiver(c) is not None else 'Not verified / not applicable; see fee wording.'),('Base and accelerated rewards; caps',lambda c:known_text(c,['cashback','reward','point','cap'])),('Domestic/international lounges and spend conditions',lambda c:known_text(c,['lounge'])),('Forex markup (+ applicable GST)',lambda c:known_text(c,['forex','foreign-currency'])),('Annual interest rate',lambda c:'45% on overdue revolving credit under the linked ICICI MITC; confirm personal terms.' if c['id']=='icici-amazon-pay-credit-card' else 'Not verified; consult the linked issuer MITC and your personal offer.')]
    for label,terms in [('UPI Scan & Pay',['upi','rupay']),('Utility bills & telecom',['utilit','telecom']),('Insurance premiums',['insurance']),('Government / NPS / tax payments',['government','nps','tax payments']),('Fuel & rent',['fuel','rent']),('Gold / jewellery',['gold purchases','jewellery','jewelry']),('School / education',['education','school'])]:
        rows.append((label,lambda c,terms=terms:known_text(c,terms)))
    table=''.join('<tr><th scope="row">'+escape(label)+'</th>'+''.join('<td>'+escape(str(getter(c)))+'</td>' for c in (left,right))+'</tr>' for label,getter in rows)
    table+='<tr><th scope="row">Official issuer MITC / reward documents</th>'+''.join('<td>'+pdf_links(c)+'</td>' for c in (left,right))+'</tr>'
    faq=[(f'Which is better in 2026: {short_name(left)} or {short_name(right)}?',note),(f'What is the annual fee and waiver spend for {short_name(left)} vs {short_name(right)}?',' '.join(f'{short_name(c)}: {c.get("annualFee","not verified")}; renewal threshold {money(waiver(c)) if waiver(c) is not None else "not verified / not applicable"}.' for c in (left,right))),(f'Does {short_name(left)} or {short_name(right)} require minimum spend for airport lounge access?',' '.join(f'{short_name(c)}: {known_text(c,["lounge"])}' for c in (left,right))),(f'Which card gives higher cashback on UPI, utilities, and online shopping?','The answer depends on eligible merchants, payment app, caps and reward redemption. Use a modelled scenario only where both cards have verified inputs. Unknown categories are not treated as zero rewards.')]
    faqs=''.join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in faq)
    exclusions=f'<section id="terms" class="comparison-block"><h2>Hidden exclusions, MITC and devaluation</h2><p>Not verified means unknown, not eligible or excluded. The sourced wording below distinguishes reward exclusions from waiver and lounge rules.</p><div class="table-scroll" role="region" aria-label="Card fees and exclusions" tabindex="0"><table><caption>Fees, reward restrictions and access rules</caption><thead><tr><th scope="col">Condition</th><th scope="col">{escape(left["name"])}</th><th scope="col">{escape(right["name"])}</th></tr></thead><tbody>{table}</tbody></table></div>{extra}<h2>Frequently asked questions</h2>{faqs}<aside class="card"><h2>Editorial review</h2><p>Prepared by the CardIQ editorial team using the dated catalogue records and linked issuer documents. Last issuer-record verification: {escape(dates)}. A catalogue date is not a fresh MITC review date.</p><a href="{origin}/methodology/">Research and comparison methodology</a><p>APR is not verified for every product. Your personal annual interest rate can differ from a general schedule. Pay the full statement balance to avoid interest; this calculator does not model borrowing costs.</p></aside></section>'
    alternatives=[c for c in cards if c['id'] in ['idfc-wow','au-ixigo-au-credit-card'] and c['id'] not in {left['id'],right['id']}]
    if len(alternatives)<2:
        alternatives += [c for c in cards if c['id'] in ['icici-amazon-pay-credit-card', 'csb-jupiter-edge-rupay'] and c['id'] not in {left['id'],right['id']} and c not in alternatives]
    fallback='<section id="alternatives" class="comparison-block"><h2>Not eligible or rejected? Consider these alternatives</h2><p>A secured or no-annual-fee card may be worth checking. These are not guaranteed or statistically high-approval offers. KYC, deposit, income and issuer conditions still apply.</p><div class="grid">'+''.join(f'<article class="card">{artwork(c)}<h3>{escape(c["name"])}</h3><p>{escape(c.get("annualFee",""))}</p><p>{escape(c.get("eligibilityNote") or c.get("availabilityNote") or "Subject to issuer approval.")}</p><p>{escape(known_text(c, ["fixed deposit", "fd-backed", "secured"], ""))}</p>{cta(c,pair,"fallback_footer_ltf",origin)}</article>' for c in alternatives[:2])+'</div></section>'
    sticky=f'<div class="comparison-sticky">{cta(left,pair,"sticky_mobile_bar",origin,short_name(left))}{cta(right,pair,"sticky_mobile_bar",origin,short_name(right))}</div>'
    body=f'<nav aria-label="Breadcrumb"><a href="{origin}/">Home</a> / <a href="{origin}/compare/">Compare cards</a></nav><h1>{escape(meta["h1"])}</h1><p>{escape(meta["metaDescription"])}</p>'+verdict+calculator+exclusions+fallback+sticky
    graph=[{'@type':'Organization','@id':origin+'/#organization','name':'CardIQ','url':origin+'/'},{'@type':'WebSite','@id':origin+'/#website','name':'CardIQ','url':origin+'/'},{'@type':'WebPage','@id':meta['canonicalUrl'],'url':meta['canonicalUrl'],'name':meta['title'],'description':meta['metaDescription'],'isPartOf':{'@id':origin+'/#website'}},{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i,'name':name,'item':url} for i,(name,url) in enumerate([('Home',origin+'/'),('Compare Cards',origin+'/compare/'),(short_name(left)+' vs '+short_name(right),meta['canonicalUrl'])],1)]},{'@type':'ItemList','itemListElement':[{'@type':'ListItem','position':i,'name':c['name'],'url':f'{origin}/cards/{c["id"]}/'} for i,c in enumerate((left,right),1)]},{'@type':'FAQPage','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in faq]}]
    for c in (left,right):
        node={'@type':'FinancialProduct','@id':f'{origin}/cards/{c["id"]}/#product','name':c['name'],'brand':{'@type':'Organization','name':c['issuer']},'feesAndCommissionsSpecification':c.get('annualFee','Confirm with issuer'),'url':f'{origin}/cards/{c["id"]}/'}
        apr = c.get('annualPercentageRate', 45 if c['id'] == 'icici-amazon-pay-credit-card' else None)
        if apr is not None:node['annualPercentageRate']=apr
        graph.append(node)
    return body,{'@context':'https://schema.org','@graph':graph}
