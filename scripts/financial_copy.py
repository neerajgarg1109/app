"""Presentation-only fee wording; spending thresholds and rewards are never taxed."""
import re


def explicit_fee_tax(text):
    text = str(text)
    text = re.sub(r'(₹[\d,]+(?:\.\d+)?)\s*(?:before GST|pre-GST|\+\s*GST)', r'\1 + 18% GST', text, flags=re.I)
    text = re.sub(r'(₹[\d,]+(?:\.\d+)?)(?![\d,.])(?=\s+(?:annually|annual fee|joining fee|renewal fee|fee\b))', r'\1 + 18% GST', text, flags=re.I)
    text = re.sub(r'(\+ 18% GST(?:\s+(?:annually|annual fee|joining fee|renewal fee))?)\s+(?:before GST|plus GST)', r'\1', text, flags=re.I)
    return text


def fee_copy(card, field='annualFee'):
    text = explicit_fee_tax(card.get(field, 'Confirm the fee with the issuer'))
    amount = card.get(field + 'Amount')
    if amount and not re.search(r'(?:18% GST|incl(?:uding|usive|\.)?[^.]{0,12}GST)', text, re.I):
        # Only annotate the first fee value; later rupee amounts can be spend thresholds.
        text = re.sub(r'₹[\d,]+(?:\.\d+)?', lambda m: m[0] + ' + 18% GST', text, count=1)
        if '18% GST' not in text:
            text = f'₹{amount:,} + 18% GST · {text}'
    return text
