"""Guard fee variants, access prerequisites and authentic artwork in this batch."""
import hashlib
import json
from pathlib import Path

from cards_seed import CARDS, recommend_cards
from restricted_access import restricted_access

ROOT = Path(__file__).resolve().parents[2]
BATCH = {c['id']: c for c in CARDS if c.get('catalogBatch') == 'verified-missing-products-2026-10-29'}


def test_new_card_artwork_matches_reviewed_official_bytes():
    assert len(BATCH) == 6
    provenance = {item['id']: item for item in json.loads((ROOT / 'docs/catalog-artwork-sources.json').read_text())}
    for card_id, card in BATCH.items():
        source = provenance[card_id]
        asset = ROOT / 'frontend/public' / card['imageUrl'].lstrip('/')
        assert asset.is_file()
        assert hashlib.sha256(asset.read_bytes()).hexdigest() == source['sha256']
        assert source['source'] == card['imageSourceUrl']
        assert card['verifiedOn'] == source['reviewedOn']


def test_virtual_and_physical_fees_are_not_combined_into_free_ownership():
    from server import _card_summary_for_client
    kiwi = BATCH['pnb-kiwi-credit-card']
    assert kiwi['annualFeeAmount'] == kiwi['joiningFeeAmount'] == 0
    assert 'virtual' in kiwi['annualFee'] and '₹750' in kiwi['annualFee']
    assert 'physical' in kiwi['joiningFee'] and '₹500' in kiwi['joiningFee']
    assert 'lifetime-free' not in kiwi['bestFor']
    assert _card_summary_for_client(kiwi)['lifetimeFree'] is False
    paisa = BATCH['sbm-paisabazaar-paisa-plus-credit-card']
    assert paisa['annualFeeAmount'] == 499
    assert '₹50,000' in paisa['annualFee']
    niyo = BATCH['sbm-niyo-global-credit-card']
    assert 'current waiver' in niyo['annualFee'] and '₹500' in niyo['annualFee']
    assert _card_summary_for_client(niyo)['lifetimeFree'] is False


def test_invitation_and_partner_access_stay_separate_and_out_of_general_quiz():
    reserve = BATCH['icici-1838-reserve-credit-card']
    assert reserve['annualFeeAmount'] == reserve['joiningFeeAmount'] == 175000
    assert restricted_access(reserve)['accessType'] == 'invite-only'
    for card_id in ('sbi-eternal-sbi-card', 'sbm-magnet-credit-card', 'sbm-niyo-global-credit-card'):
        assert BATCH[card_id]['recommendationEligible'] is False
        assert restricted_access(BATCH[card_id])['accessType'] != 'invite-only'
    restricted_ids = {c['id'] for c in BATCH.values() if c['recommendationEligible'] is False}
    answers = dict(goal='travel', usage='flights', priority='lounge', fee='premium', spend='high', creditRoute='regular')
    assert not restricted_ids.intersection(item['card']['id'] for item in recommend_cards(answers, CARDS))
    for card in BATCH.values():
        if card['issuer'] == 'SBM Bank India':
            assert card['secured'] is True
