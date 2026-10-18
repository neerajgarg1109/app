"""Shared restricted-card access classification for API and static publishing."""
from typing import Optional


def restricted_access(card: dict) -> Optional[dict]:
    text = " ".join(str(value) for value in (
        card.get("name"), card.get("availabilityNote"), card.get("eligibilityNote"),
        card.get("coBrandPartner"), *(card.get("highlights") or []),
    ) if value).lower()
    if card.get("recommendationEligible") is not False and not any(term in text for term in ("invite-only", "invitation-only")):
        return None
    if any(term in text for term in ("invite-only", "invitation-only", "by invitation")):
        kind, label = "invite-only", "Invitation only"
    elif any(term in text for term in ("existing cardholder", "existing customer", "selected existing", "upgrade", "swipeup", "premier banking", "aspire banking", "signature banking", "cred member")):
        kind, label = "existing-relationship", "Existing relationship required"
    elif any(term in text for term in ("defence", "armed forces", "doctor", "medical professional", "government employee", "salaried professional")):
        kind, label = "segment-restricted", "Restricted customer segment"
    elif any(term in text for term in ("partner bank", "bank branch", "no online application", "available through")):
        kind, label = "partner-channel", "Partner or branch channel"
    else:
        kind, label = "issuer-discretion", "Issuer-selected access"
    explanation = card.get("availabilityNote") or card.get("eligibilityNote") or "Access is controlled by the issuer and may not be available through a public application route."
    return {"accessType": kind, "accessLabel": label, "accessExplanation": explanation}
