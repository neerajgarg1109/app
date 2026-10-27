"""Access classification must distinguish invitations from other restrictions."""
import json
from pathlib import Path
import pytest
from restricted_access import restricted_access


def test_infinia_is_invitation_only_in_catalog():
    cards = json.loads((Path(__file__).parents[1] / "cards_catalog.json").read_text())
    card = next(card for card in cards if card["id"] == "hdfc-infinia-credit-card")
    assert restricted_access(card)["accessType"] == "invite-only"
    assert "invitation only" in restricted_access(card)["accessExplanation"]
    assert card["recommendationEligible"] is False


@pytest.mark.parametrize("wording", ["Invite-only", "Invitation-only", "Invite only", "Invitation only", "Available by invitation"])
def test_invitation_wording_is_consistent_even_without_quiz_exclusion(wording):
    assert restricted_access({"availabilityNote": wording})["accessType"] == "invite-only"


def test_relationship_cards_are_not_invitation_only():
    card = {"recommendationEligible": False, "availabilityNote": "Only for HSBC Premier banking customers."}
    assert restricted_access(card)["accessType"] == "existing-relationship"
