"""Direct email delivery, independent of the original hosting platform."""
import os
from email.utils import formataddr

import httpx


class EmailConfigurationError(Exception):
    pass


class EmailDeliveryError(Exception):
    pass


async def deliver_email(*, to, subject, html, reply_to=None):
    provider = os.environ.get("EMAIL_PROVIDER", "disabled").strip().lower()
    key = os.environ.get("RESEND_API_KEY", "").strip()
    sender = os.environ.get("EMAIL_FROM_ADDRESS", "").strip()
    if provider != "resend" or not key or "@" not in sender:
        raise EmailConfigurationError("Configure an email provider and verified sender")
    payload = {
        "from": formataddr((os.environ.get("EMAIL_FROM_NAME", "CardIQ"), sender)),
        "to": [to], "subject": subject, "html": html,
    }
    address = reply_to or os.environ.get("EMAIL_REPLY_TO")
    if address:
        payload["reply_to"] = address
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {key}"},
                json=payload,
            )
        response.raise_for_status()
        email_id = response.json().get("id")
        if not isinstance(email_id, str) or not email_id.strip():
            raise EmailDeliveryError("Provider returned no message ID")
        return email_id
    except (httpx.HTTPError, ValueError, AttributeError):
        # Do not expose provider responses, recipient addresses, or credentials.
        raise EmailDeliveryError("Email delivery failed") from None
