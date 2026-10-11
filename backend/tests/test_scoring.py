"""Focused scoring invariants independent of MongoDB and HTTP."""
from copy import deepcopy

import pytest

from cards_seed import CARDS, recommend_cards


BASE = {
    "goal": "cashback", "spend": "mid", "fee": "worth",
    "usage": "online", "priority": "cashback", "creditRoute": "either",
}


def test_secured_route_prioritises_an_fd_backed_card():
    result = recommend_cards({**BASE, "creditRoute": "secured"}, CARDS)
    assert result[0]["card"]["secured"] is True
    assert any("FD-backed route" in reason for reason in result[0]["reasons"])


def test_regular_route_does_not_return_a_secured_top_match():
    for goal in ("cashback", "travel", "shopping", "fuel"):
        result = recommend_cards({**BASE, "goal": goal, "creditRoute": "regular"}, CARDS)
        assert result[0]["card"]["secured"] is False


def test_show_both_is_neutral_relative_to_omitting_the_route():
    with_route = recommend_cards({**BASE, "creditRoute": "either"}, CARDS)
    without_route = recommend_cards({key: value for key, value in BASE.items() if key != "creditRoute"}, CARDS)
    assert [item["card"]["id"] for item in with_route] == [item["card"]["id"] for item in without_route]


def test_historical_credit_answers_still_affect_legacy_results():
    secured = next(card for card in CARDS if card.get("secured"))
    premium = next(card for card in CARDS if card.get("creditReq") == "excellent" and not card.get("secured"))
    new_credit = recommend_cards({**BASE, "creditRoute": None, "credit": "new"}, [secured, premium])
    excellent_credit = recommend_cards({**BASE, "creditRoute": None, "credit": "excellent"}, [secured, premium])
    assert new_credit[0]["card"]["id"] == secured["id"]
    assert excellent_credit


@pytest.mark.parametrize("profile", [
    {"goal": "travel", "spend": "high", "fee": "premium", "usage": "flights", "priority": "lounge", "creditRoute": "regular"},
    {"goal": "shopping", "spend": "mid", "fee": "worth", "usage": "dining", "priority": "rewards", "creditRoute": "either"},
    {"goal": "fuel", "spend": "low", "fee": "free", "usage": "fuel", "priority": "cashback", "creditRoute": "regular"},
    {"goal": "cashback", "spend": "low", "fee": "free", "usage": "online", "priority": "cashback", "creditRoute": "secured"},
])
def test_value_estimates_are_internally_consistent(profile):
    for item in recommend_cards(profile, CARDS)[:25]:
        value = item["valueEstimate"]
        assert 35 <= item["confidence"] <= 99
        assert value["grossLow"] <= value["grossHigh"]
        assert value["netLow"] <= value["netHigh"]
        assert value["annualSpendAssumption"] >= 0
        assert value["effectiveAnnualFee"] in {0, value["annualFee"]}
        assert value["headlinePotential"] >= value["grossHigh"]


def test_personalised_spend_inputs_drive_the_value_model():
    low = recommend_cards({**BASE, "monthlySpend": "20000", "onlineSpend": "10000"}, CARDS)[0]
    high = recommend_cards({**BASE, "monthlySpend": "100000", "onlineSpend": "70000"}, CARDS)[0]
    assert low["valueEstimate"]["isPersonalized"] is True
    assert high["valueEstimate"]["annualSpendAssumption"] == 1_200_000
    assert high["valueEstimate"]["grossHigh"] > low["valueEstimate"]["grossHigh"]


def test_unavailable_and_restricted_cards_are_filtered_but_history_can_resolve_them():
    card = deepcopy(CARDS[0])
    card.update(id="unavailable-test", active=False, applicationsOpen=False, recommendationEligible=False)
    assert recommend_cards(BASE, [card]) == []
    assert recommend_cards(BASE, [card], include_unavailable=True)[0]["card"]["id"] == "unavailable-test"


def test_free_fee_preference_penalises_paid_equivalent():
    free = deepcopy(CARDS[0])
    paid = deepcopy(CARDS[0])
    free.update(id="free-copy", name="Free Copy", feeType="free", annualFeeAmount=0)
    paid.update(id="paid-copy", name="Paid Copy", feeType="worth", annualFeeAmount=999)
    result = recommend_cards({**BASE, "fee": "free"}, [paid, free])
    assert result[0]["card"]["id"] == "free-copy"
