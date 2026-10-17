from fastapi import FastAPI, APIRouter, HTTPException, Header, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import re
import ipaddress
import logging
import httpx
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Dict, Optional, Any
import uuid
import secrets
import hashlib
import unicodedata
from datetime import datetime, timezone, timedelta

from cards_seed import seed_cards, recommend_cards, CATALOG_QUERY, RECOMMENDABLE_QUERY

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="cardIQ API", version="1.0.0")
api_router = APIRouter(prefix="/api")

logger = logging.getLogger(__name__)


@app.get("/")
async def service_root():
    """Give people opening the API port directly a useful landing response."""
    return {
        "message": "cardIQ API",
        "version": "v1",
        "api": "/api/",
        "docs": "/docs",
        "customer_portal": PUBLIC_APP_URL,
    }

# ---------------- Email (Emergent managed Resend) ----------------
EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ.get("EMERGENT_EMAIL_KEY")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "cardIQ")
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")
ADMIN_VIEWER_TOKEN = os.environ.get("ADMIN_VIEWER_TOKEN")
ADMIN_EDITOR_TOKEN = os.environ.get("ADMIN_EDITOR_TOKEN")
ADMIN_PUBLISHER_TOKEN = os.environ.get("ADMIN_PUBLISHER_TOKEN")
PUBLIC_APP_URL = os.environ.get("PUBLIC_APP_URL", "https://cardiq.in").rstrip("/")

_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "goo.gl", "rebrand.ly")
_CRED_ASK = ("reply with your password", "reply with the code", "send your password", "cvv",
             "send us your password", "enter your password below", "confirm your card number",
             "your full card number", "seed phrase", "recovery phrase", "verify your card",
             "social security number", "confirm your bank details")
_HOSTISH = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def _host_ok(host: str) -> bool:
    if not host or "xn--" in host:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return not any(host == s or host.endswith("." + s) for s in _SHORTENERS)


def _same_site(shown: str, real: str) -> bool:
    return shown == real or real.endswith("." + shown) or shown.endswith("." + real)


class _EmailScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.urls, self.anchors = set(), [], []
        self._href, self._text = None, []

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag.lower())
        self.urls += [v for k, v in attrs if k.lower() in ("href", "src") and v]
        if tag.lower() == "a":
            self._href = dict((k.lower(), v) for k, v in attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append((self._href, "".join(self._text)))
            self._href, self._text = None, []


def _assert_safe_email(subject: str, html: str) -> None:
    scan = _EmailScan()
    scan.feed(html)
    if scan.tags & {"form", "input", "textarea", "select"}:
        raise ValueError("No forms or input fields in email (G2)")
    body = f"{subject}\n{html}".lower()
    for p in _CRED_ASK:
        if p in body:
            raise ValueError(f"Email asks the recipient for credentials: {p!r} (G2)")
    for url in scan.urls:
        low = url.strip().lower()
        if low.startswith(("mailto:", "tel:", "cid:", "#")):
            continue
        if not low.startswith("https://"):
            raise ValueError(f"Email links/assets must be absolute https: {url!r} (G3)")
        host = urlparse(low).hostname or ""
        if not _host_ok(host) or urlparse(low).username is not None:
            raise ValueError(f"Shortened, numeric-host or credential-bearing URL: {url!r} (G3)")
    for href, text in scan.anchors:
        real = urlparse(href.strip().lower()).hostname or ""
        if not real:
            continue
        for m in _HOSTISH.finditer(text):
            if not _same_site(m.group(1).lower(), real):
                raise ValueError(f"Anchor text {m.group(1)!r} != real link host {real!r} (G3)")


async def send_email(*, to: str, subject: str, html: str, reply_to: Optional[str] = None) -> Optional[str]:
    _assert_safe_email(subject, html)
    if not EMAIL_KEY:
        raise HTTPException(status_code=500, detail="Email not configured")
    payload = {"to": [to], "subject": subject, "html": html, "from_name": EMAIL_FROM_NAME}
    if reply_to or EMAIL_REPLY_TO:
        payload["contact_email"] = reply_to or EMAIL_REPLY_TO
    try:
        async with httpx.AsyncClient(timeout=30) as client_http:
            resp = await client_http.post(
                f"{EMAIL_BASE_URL}/api/v1/email/send",
                headers={"X-Email-Key": EMAIL_KEY},
                json=payload,
            )
        resp.raise_for_status()
        return resp.json().get("id")
    except httpx.HTTPStatusError as e:
        logger.error(f"Email send failed: {e.response.status_code} {e.response.text}")
        raise HTTPException(status_code=502, detail="Failed to send email")
    except Exception as e:
        logger.error(f"Email send error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send email")


def _build_recommendation_email(name: str, card: Dict[str, Any], reasons: List[str]) -> str:
    benefits = "".join(
        f'<li style="margin:6px 0;color:#0f1a17;font-size:14px">{escape(h)}</li>'
        for h in card.get("highlights", [])
    )
    reason_html = ""
    if reasons:
        rs = "".join(
            f'<li style="margin:4px 0;color:#55615c;font-size:14px">{escape(r)}</li>'
            for r in reasons
        )
        reason_html = (
            f'<p style="margin:18px 0 6px;font-weight:700;color:#0f1a17">Why it fits you</p>'
            f'<ul style="padding-left:18px;margin:0">{rs}</ul>'
        )
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:#f6f7f5;padding:24px"><tr><td align="center">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="max-width:520px;background:#ffffff;border-radius:16px;overflow:hidden;'
        f'font-family:Arial,Helvetica,sans-serif">'
        f'<tr><td style="background:#0d9488;padding:20px 24px">'
        f'<span style="color:#ffffff;font-size:20px;font-weight:800">card'
        f'<span style="color:#5eead4">IQ</span></span></td></tr>'
        f'<tr><td style="padding:24px">'
        f'<p style="margin:0 0 4px;color:#55615c;font-size:13px">Hi {escape(name)}, here is your best match</p>'
        f'<h1 style="margin:0 0 4px;color:#0f1a17;font-size:24px">{escape(card["name"])}</h1>'
        f'<p style="margin:0 0 16px;color:#55615c;font-size:14px">{escape(card.get("tagline",""))}</p>'
        f'<table role="presentation" width="100%" style="border:1px solid #e6e8e3;border-radius:12px">'
        f'<tr><td style="padding:14px 16px">'
        f'<p style="margin:0;color:#0f1a17;font-weight:700;font-size:14px">{escape(card.get("rewardLine",""))}</p>'
        f'<p style="margin:4px 0 0;color:#55615c;font-size:13px">Annual fee: {escape(card.get("annualFee",""))}'
        f' &middot; Rated {escape(str(card.get("rating","")))}/5</p></td></tr></table>'
        f'{reason_html}'
        f'<p style="margin:18px 0 6px;font-weight:700;color:#0f1a17">Key benefits</p>'
        f'<ul style="padding-left:18px;margin:0">{benefits}</ul>'
        f'<p style="margin:22px 0 6px;color:#55615c;font-size:12px">This recommendation is based on the answers '
        f'you shared with cardIQ. We are not sponsored by any bank.</p>'
        f'<p style="margin:0;color:#888;font-size:12px">Sent by cardIQ. We never ask for your password or card '
        f'details by email.</p>'
        f'</td></tr></table></td></tr></table>'
    )


def _build_welcome_email(name: str, card_name: str) -> str:
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:#f6f7f5;padding:24px"><tr><td align="center">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="max-width:520px;background:#ffffff;border-radius:16px;overflow:hidden;'
        f'font-family:Arial,Helvetica,sans-serif">'
        f'<tr><td style="background:#0d9488;padding:20px 24px">'
        f'<span style="color:#ffffff;font-size:20px;font-weight:800">card'
        f'<span style="color:#5eead4">IQ</span></span></td></tr>'
        f'<tr><td style="padding:24px">'
        f'<h1 style="margin:0 0 8px;color:#0f1a17;font-size:22px">Welcome, {escape(name)}!</h1>'
        f'<p style="margin:0 0 12px;color:#55615c;font-size:14px">Thanks for using cardIQ. We just '
        f'matched you with <strong style="color:#0f1a17">{escape(card_name)}</strong> based on your answers '
        f'&mdash; an honest, unbiased pick that fits your life.</p>'
        f'<p style="margin:0 0 12px;color:#55615c;font-size:14px">A full breakdown of your match and its '
        f'benefits is on your results screen. You can revisit it any time.</p>'
        f'<p style="margin:18px 0 6px;color:#55615c;font-size:12px">We are not sponsored by any bank, and '
        f'we will never share your details or spam you with calls.</p>'
        f'<p style="margin:0;color:#888;font-size:12px">Sent by cardIQ. We never ask for your password or '
        f'card details by email.</p>'
        f'</td></tr></table></td></tr></table>'
    )



# ---------------- Models ----------------
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


class LeadIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    contact_consent: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = " ".join(value.split())
        letters = [char for char in value if char.isalpha()]
        if not 2 <= len(value) <= 80 or len(letters) < 2:
            raise ValueError("Enter a name between 2 and 80 characters")
        if any(not (char.isalpha() or unicodedata.category(char).startswith("M") or char in " .'-") for char in value):
            raise ValueError("Name can contain letters, spaces, apostrophes, hyphens and full stops only")
        compact = "".join(letters).casefold()
        if compact in {"asdf", "qwerty", "zxcv", "test", "unknown", "none", "random"} or re.search(r"(.)\1{3,}", compact):
            raise ValueError("Enter your real name")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        digits = re.sub(r"[\s()\-]", "", value)
        if digits.startswith("+91"):
            digits = digits[3:]
        elif digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        if not re.fullmatch(r"[6-9]\d{9}", digits):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return f"+91{digits}"


class QuizSubmitIn(BaseModel):
    answers: Dict[str, str]
    lead: Optional[LeadIn] = None


class CompareIn(BaseModel):
    ids: List[str]


class ApplyClickIn(BaseModel):
    result_id: Optional[str] = None


class CardReportIn(BaseModel):
    issue: str
    email: Optional[EmailStr] = None


class ReviewFollowupIn(BaseModel):
    email: EmailStr
    result_id: Optional[str] = None
    review_consent: bool


class ExperienceFeedbackIn(BaseModel):
    rating: int
    feedback: Optional[str] = None
    result_id: Optional[str] = None
    card_id: Optional[str] = None


class ProductEventIn(BaseModel):
    event: str
    session_id: str
    result_id: Optional[str] = None
    card_id: Optional[str] = None
    channel: Optional[str] = None
    page_type: Optional[str] = None

    @field_validator("event")
    @classmethod
    def validate_event(cls, value: str) -> str:
        allowed = {"landing_view", "quiz_started", "result_viewed", "lead_submitted", "apply_clicked", "content_shared"}
        if value not in allowed:
            raise ValueError("Unsupported product event")
        return value

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in {"whatsapp", "x", "facebook", "copy", "native"}:
            raise ValueError("Unsupported share channel")
        return value

    @field_validator("card_id")
    @classmethod
    def validate_card_id(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not re.fullmatch(r"[a-z0-9-]{1,120}", value):
            raise ValueError("Invalid card identifier")
        return value

    @field_validator("page_type")
    @classmethod
    def validate_page_type(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in {"card", "issuer", "category", "article", "result"}:
            raise ValueError("Unsupported page type")
        return value

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_-]{16,80}", value):
            raise ValueError("Invalid anonymous session identifier")
        return value


class CardholderReviewIn(BaseModel):
    overall: int
    rewards: int
    redemption: int
    service: int
    app_experience: int
    acceptance: int
    current_holder: bool
    comments: Optional[str] = None


class ReviewModerationIn(BaseModel):
    status: str


class ApplyLinkIn(BaseModel):
    apply_url: Optional[str] = None


class AdminCardIn(BaseModel):
    name: str
    issuer: str
    variants: List[str] = Field(default_factory=list)
    productGroupId: Optional[str] = None
    variantName: Optional[str] = None
    network: str = "Issuer-selected variant"
    tagline: str = ""
    annualFee: str = "No annual fee"
    annualFeeAmount: int = 0
    joiningFee: str = "No joining fee"
    joiningFeeAmount: int = 0
    rewardLine: str
    highlights: List[str] = Field(default_factory=list)
    welcomeBenefits: List[str] = Field(default_factory=list)
    milestoneBenefits: List[str] = Field(default_factory=list)
    loungeBenefits: List[str] = Field(default_factory=list)
    exclusions: List[str] = Field(default_factory=list)
    rewardCurrency: Optional[str] = None
    rewardRedemption: Optional[str] = None
    forexMarkup: Optional[str] = None
    fuelBenefits: Optional[str] = None
    eligibilityNote: Optional[str] = None
    sourceUrls: List[str] = Field(default_factory=list)
    bestFor: List[str] = Field(default_factory=list)
    feeType: str = "free"
    minSpend: str = "low"
    creditReq: str = "good"
    rating: float = 4.0
    applyUrl: str
    imageUrl: Optional[str] = None
    active: bool = True
    applicationsOpen: bool = True


class RecommendationPreviewIn(BaseModel):
    answers: Dict[str, str]


def _clean(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


def _token_expired(value: Optional[datetime]) -> bool:
    if not value:
        return True
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value < datetime.now(timezone.utc)


def _card_for_client(card: dict) -> dict:
    """Expose an admin override as applyUrl while retaining the sourced issuer URL."""
    public = dict(card)
    override = public.pop("applyUrlOverride", None)
    public["officialApplyUrl"] = public.get("applyUrl")
    if override:
        public["applyUrl"] = override
    return public


def _require_admin(token: Optional[str], minimum: str = "viewer") -> str:
    roles = {ADMIN_VIEWER_TOKEN: "viewer", ADMIN_EDITOR_TOKEN: "editor", ADMIN_PUBLISHER_TOKEN: "publisher", ADMIN_TOKEN: "owner"}
    roles.pop(None, None)
    role = roles.get(token)
    levels = {"viewer": 0, "editor": 1, "publisher": 2, "owner": 3}
    if not role:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if levels[role] < levels[minimum]:
        raise HTTPException(status_code=403, detail=f"{minimum.title()} permission required")
    return role


def _validated_apply_url(value: Optional[str]) -> Optional[str]:
    value = (value or "").strip()
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="Apply link must be an absolute HTTPS URL")
    if len(value) > 2048:
        raise HTTPException(status_code=422, detail="Apply link is too long")
    return value


def _admin_card_doc(payload: AdminCardIn, card_id: str, existing: Optional[dict] = None) -> dict:
    values = payload.dict()
    name, issuer = values["name"].strip(), values["issuer"].strip()
    if not name or not issuer or not values["rewardLine"].strip():
        raise HTTPException(status_code=422, detail="Name, issuer and reward summary are required")
    if values["feeType"] not in {"free", "worth", "premium"}:
        raise HTTPException(status_code=422, detail="Invalid fee type")
    if values["minSpend"] not in {"low", "mid", "high", "vhigh"}:
        raise HTTPException(status_code=422, detail="Invalid minimum spend tier")
    if values["creditReq"] not in {"new", "fair", "good", "excellent"}:
        raise HTTPException(status_code=422, detail="Invalid credit requirement")
    if not 0 <= values["rating"] <= 5 or values["annualFeeAmount"] < 0 or values["joiningFeeAmount"] < 0:
        raise HTTPException(status_code=422, detail="Fees and rating must be valid positive values")
    values["applyUrl"] = _validated_apply_url(values["applyUrl"])
    values["name"], values["issuer"] = name, issuer
    values["variants"] = list(dict.fromkeys(v.strip() for v in values["variants"] if v.strip()))
    for list_field in ("highlights", "welcomeBenefits", "milestoneBenefits", "loungeBenefits", "exclusions"):
        values[list_field] = [v.strip() for v in values[list_field] if v.strip()]
    values["bestFor"] = list(dict.fromkeys(v.strip().lower() for v in values["bestFor"] if v.strip()))
    values["sourceUrls"] = list(dict.fromkeys(filter(None, [_validated_apply_url(v) for v in values["sourceUrls"]])))
    for text_field in ("rewardCurrency", "rewardRedemption", "forexMarkup", "fuelBenefits", "eligibilityNote"):
        values[text_field] = (values.get(text_field) or "").strip() or None
    values["productGroupId"] = (values.get("productGroupId") or "").strip() or None
    values["variantName"] = (values.get("variantName") or "").strip() or None
    values.update({
        "id": card_id,
        "palette": (existing or {}).get("palette", ["#172554", "#1e40af"]),
        "accent": (existing or {}).get("accent", "#fbbf24"),
        "ratingBasis": (existing or {}).get("ratingBasis", "Neutral cardIQ editorial baseline, not a customer or issuer rating."),
        "sourceUrls": list(dict.fromkeys([values["applyUrl"], *values["sourceUrls"], *((existing or {}).get("sourceUrls", []))])),
        "verifiedOn": datetime.now(timezone.utc).date().isoformat(),
        "availabilityNote": (existing or {}).get("availabilityNote", "Subject to issuer availability and approval."),
        "secured": (existing or {}).get("secured", False),
        "termsNote": (existing or {}).get("termsNote", "Eligible transactions only; issuer exclusions, reward caps and benefit conditions apply."),
        "adminManaged": True,
    })
    return values


def _admin_card(card: dict) -> dict:
    stored = _clean(dict(card))
    draft = stored.get("draft")
    public = {**stored, **draft} if draft else stored
    public.setdefault("variants", [public.get("network")] if public.get("network") else [])
    public.update({
        "official_apply_url": public.get("applyUrl"),
        "custom_apply_url": public.get("applyUrlOverride"),
        "effective_apply_url": public.get("applyUrlOverride") or public.get("applyUrl"),
        "has_draft": bool(draft),
        "publication_status": "draft" if draft else stored.get("publicationStatus", "published"),
        "is_new_draft": bool(draft and stored.get("publicationStatus") == "draft"),
        "draft": draft,
    })
    return public


# ---------------- Routes ----------------
@api_router.get("/")
async def root():
    return {"message": "cardIQ API"}


@api_router.get("/cards")
async def get_cards():
    cards = await db.cards.find(CATALOG_QUERY, {"_id": 0}).to_list(None)
    return [_card_for_client(card) for card in cards]


@api_router.post("/cards/{card_id}/apply-click")
async def track_apply_click(card_id: str, payload: ApplyClickIn):
    card = await db.cards.find_one({"id": card_id, **CATALOG_QUERY}, {"_id": 1})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    await db.apply_events.insert_one({"event_id": str(uuid.uuid4()), "card_id": card_id, "result_id": payload.result_id, "created_at": datetime.now(timezone.utc)})
    return {"status": "recorded"}


@api_router.post("/cards/{card_id}/report")
async def report_card_information(card_id: str, payload: CardReportIn):
    issue = payload.issue.strip()
    if len(issue) < 10 or len(issue) > 1000:
        raise HTTPException(status_code=422, detail="Please describe the issue in 10–1,000 characters")
    if not await db.cards.find_one({"id": card_id}, {"_id": 1}):
        raise HTTPException(status_code=404, detail="Card not found")
    await db.card_reports.insert_one({"report_id": str(uuid.uuid4()), "card_id": card_id, "issue": issue, "email": str(payload.email) if payload.email else None, "status": "open", "created_at": datetime.now(timezone.utc)})
    return {"status": "received"}


@api_router.post("/cards/{card_id}/review-followup")
async def create_review_followup(card_id: str, payload: ReviewFollowupIn):
    if not payload.review_consent:
        raise HTTPException(status_code=422, detail="Review-reminder consent is required")
    if not await db.cards.find_one({"id": card_id, **CATALOG_QUERY}, {"_id": 1}):
        raise HTTPException(status_code=404, detail="Card not found")
    now = datetime.now(timezone.utc)
    followup_id = str(uuid.uuid4())
    await db.review_followups.update_one(
        {"email": str(payload.email).lower(), "card_id": card_id},
        {"$set": {"followup_id": followup_id, "email": str(payload.email).lower(), "card_id": card_id,
                  "result_id": payload.result_id, "review_consent": True, "marketing_consent": False,
                  "due_at": now + timedelta(days=75), "updated_at": now, "reminder_sent": False,
                  "review_submitted": False}, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    return {"status": "scheduled", "due_in_days": 75}


@api_router.post("/experience-feedback", status_code=201)
async def create_experience_feedback(payload: ExperienceFeedbackIn):
    feedback = (payload.feedback or "").strip()
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=422, detail="Rating must be between 1 and 5")
    if len(feedback) > 1500:
        raise HTTPException(status_code=422, detail="Feedback must be 1,500 characters or fewer")
    if payload.card_id and not await db.cards.find_one({"id": payload.card_id}, {"_id": 1}):
        raise HTTPException(status_code=404, detail="Card not found")
    await db.experience_feedback.insert_one({
        "feedback_id": str(uuid.uuid4()),
        "rating": payload.rating,
        "feedback": feedback or None,
        "result_id": payload.result_id,
        "card_id": payload.card_id,
        "created_at": datetime.now(timezone.utc),
    })
    return {"status": "received"}


@api_router.post("/product-events", status_code=202)
async def record_product_event(payload: ProductEventIn):
    """Record a deduplicated, anonymous funnel event without arbitrary metadata."""
    now = datetime.now(timezone.utc)
    dimensions = {"event": payload.event, "session_id": payload.session_id, "result_id": payload.result_id,
                  "card_id": payload.card_id, "channel": payload.channel, "page_type": payload.page_type}
    await db.product_events.update_one(
        dimensions,
        {"$setOnInsert": {
            "event_id": str(uuid.uuid4()),
            "event": payload.event,
            "session_id": payload.session_id,
            "result_id": payload.result_id,
            "card_id": payload.card_id,
            "channel": payload.channel,
            "page_type": payload.page_type,
            "created_at": now,
        }},
        upsert=True,
    )
    return {"status": "recorded"}


@api_router.get("/cards/{card_id}/community-rating")
async def community_rating(card_id: str):
    reviews = await db.cardholder_reviews.find({"card_id": card_id, "status": "approved"}, {"_id": 0}).to_list(None)
    count = len(reviews)
    if count < 20:
        return {"published": False, "count": count, "minimum": 20}
    dimensions = ["overall", "rewards", "redemption", "service", "app_experience", "acceptance"]
    averages = {key: round(sum(review[key] for review in reviews) / count, 1) for key in dimensions}
    return {"published": True, "count": count, "minimum": 20, **averages}


@api_router.get("/reviews/invite/{token}")
async def review_invitation(token: str):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    invite = await db.review_followups.find_one({"token_hash": token_hash}, {"_id": 0})
    if not invite or invite.get("review_submitted") or _token_expired(invite.get("token_expires_at")):
        raise HTTPException(status_code=404, detail="Review link is invalid or expired")
    card = await db.cards.find_one({"id": invite["card_id"]}, {"_id": 0, "id": 1, "name": 1, "issuer": 1})
    return {"card": card}


@api_router.post("/reviews/invite/{token}")
async def submit_cardholder_review(token: str, payload: CardholderReviewIn):
    ratings = [payload.overall, payload.rewards, payload.redemption, payload.service, payload.app_experience, payload.acceptance]
    if not payload.current_holder or any(value < 1 or value > 5 for value in ratings):
        raise HTTPException(status_code=422, detail="Current cardholder confirmation and ratings from 1–5 are required")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    invite = await db.review_followups.find_one({"token_hash": token_hash, "review_submitted": False})
    if not invite or _token_expired(invite.get("token_expires_at")):
        raise HTTPException(status_code=404, detail="Review link is invalid or expired")
    review = payload.dict()
    review.update({"review_id": str(uuid.uuid4()), "card_id": invite["card_id"], "followup_id": invite["followup_id"],
                   "status": "pending", "created_at": datetime.now(timezone.utc)})
    await db.cardholder_reviews.insert_one(review)
    await db.review_followups.update_one({"followup_id": invite["followup_id"]}, {"$set": {"review_submitted": True}, "$unset": {"token_hash": ""}})
    return {"status": "submitted_for_review"}


@api_router.get("/cards/{card_id}")
async def get_card(card_id: str):
    card = await db.cards.find_one({"id": card_id}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return _card_for_client(card)


@api_router.post("/cards/compare")
async def compare_cards(payload: CompareIn):
    if not payload.ids:
        raise HTTPException(status_code=400, detail="No card ids provided")
    cards = await db.cards.find({"id": {"$in": payload.ids}}, {"_id": 0}).to_list(20)
    order = {cid: i for i, cid in enumerate(payload.ids)}
    cards.sort(key=lambda c: order.get(c["id"], 999))
    return [_card_for_client(card) for card in cards]


@api_router.post("/quiz/submit")
async def submit_quiz(payload: QuizSubmitIn):
    cards = await db.cards.find(RECOMMENDABLE_QUERY, {"_id": 0}).to_list(None)
    if not cards:
        raise HTTPException(status_code=503, detail="Card catalog unavailable")

    scored = recommend_cards(payload.answers, [_card_for_client(card) for card in cards])
    if not scored:
        raise HTTPException(status_code=503, detail="No cards currently available for application")
    top = scored[0]
    result_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    lead_id = None
    if payload.lead:
        lead_id = str(uuid.uuid4())
        lead_doc = {
            "lead_id": lead_id,
            "name": payload.lead.name,
            "email": payload.lead.email,
            "phone": payload.lead.phone,
            "contact_consent": payload.lead.contact_consent,
            "consent_recorded_at": now if payload.lead.contact_consent else None,
            "result_id": result_id,
            "created_at": now,
        }
        await db.leads.insert_one(dict(lead_doc))

    result_doc = {
        "result_id": result_id,
        "answers": payload.answers,
        "recommended_card_id": top["card"]["id"],
        "scored_ids": [s["card"]["id"] for s in scored],
        # Keep shared results and emails stable when issuer facts change later.
        "scored": scored,
        "lead_id": lead_id,
        "email_sent": False,
        "created_at": now,
    }
    await db.quiz_results.insert_one(dict(result_doc))

    # Mark any matching partial session as completed (so no reminder is sent)
    if payload.lead:
        await db.partial_sessions.update_one(
            {"email": payload.lead.email}, {"$set": {"completed": True}}
        )

    # Best-effort welcome email the moment a lead submits (does not block the response on failure)
    if payload.lead:
        try:
            welcome_html = _build_welcome_email(payload.lead.name, top["card"]["name"])
            await send_email(
                to=payload.lead.email,
                subject="Welcome to cardIQ — your match is ready",
                html=welcome_html,
            )
            await db.quiz_results.update_one({"result_id": result_id}, {"$set": {"welcome_sent": True}})
        except Exception as e:
            logger.error(f"Welcome email failed (non-fatal): {e}")

    return {
        "result_id": result_id,
        "scored": [
            {"card": s["card"], "score": s["score"], "confidence": s.get("confidence"), "reasons": s["reasons"], "valueEstimate": s.get("valueEstimate")}
            for s in scored
        ],
    }


@api_router.post("/results/{result_id}/lead")
async def attach_result_lead(result_id: str, payload: LeadIn):
    result = await db.quiz_results.find_one({"result_id": result_id}, {"_id": 0})
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    lead_id = result.get("lead_id") or str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await db.leads.update_one(
        {"lead_id": lead_id},
        {"$set": {
            "lead_id": lead_id,
            "name": payload.name,
            "email": payload.email,
            "phone": payload.phone,
            "contact_consent": payload.contact_consent,
            "consent_recorded_at": now if payload.contact_consent else None,
            "result_id": result_id,
            "created_at": now,
        }},
        upsert=True,
    )
    await db.quiz_results.update_one({"result_id": result_id}, {"$set": {"lead_id": lead_id}})
    await db.partial_sessions.update_one(
        {"email": payload.email}, {"$set": {"completed": True}}
    )
    return {"status": "saved", "lead_id": lead_id}


async def scored_result(result):
    if result.get("scored"):
        scored = result["scored"]
        ids = [s["card"]["id"] for s in scored]
        current = await db.cards.find(
            {"id": {"$in": ids}}, {"_id": 0, "id": 1, "applyUrlOverride": 1, "imageUrl": 1, "imageSourceUrl": 1}
        ).to_list(None)
        current_by_id = {c["id"]: c for c in current}
        refreshed = []
        for item in scored:
            updated = dict(item)
            card = dict(item["card"])
            official = card.get("officialApplyUrl", card.get("applyUrl"))
            card["officialApplyUrl"] = official
            latest = current_by_id.get(card["id"], {})
            card["applyUrl"] = latest.get("applyUrlOverride") or official
            if latest.get("imageUrl"):
                card["imageUrl"] = latest["imageUrl"]
                card["imageSourceUrl"] = latest.get("imageSourceUrl")
            updated["card"] = card
            refreshed.append(updated)
        return refreshed
    # Older results store IDs only. Archived demo records remain available here.
    ids = result.get("scored_ids")
    query = {"id": {"$in": ids}} if ids else RECOMMENDABLE_QUERY
    cards = await db.cards.find(query, {"_id": 0}).to_list(None)
    scored = recommend_cards(
        result["answers"], [_card_for_client(card) for card in cards],
        include_unavailable=bool(ids),
    )
    if not scored:
        raise HTTPException(status_code=410, detail="Cards for this result are no longer available")
    return scored


@api_router.get("/results/{result_id}")
async def get_result(result_id: str):
    result = await db.quiz_results.find_one({"result_id": result_id}, {"_id": 0})
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    scored = await scored_result(result)
    return {
        "result_id": result_id,
        "scored": [
            {"card": s["card"], "score": s["score"], "confidence": s.get("confidence"), "reasons": s["reasons"], "valueEstimate": s.get("valueEstimate")}
            for s in scored
        ],
    }


@api_router.post("/results/{result_id}/email")
async def email_result(result_id: str):
    """Send the recommendation to the lead email stored server-side (G4: no caller email)."""
    result = await db.quiz_results.find_one({"result_id": result_id}, {"_id": 0})
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    lead = await db.leads.find_one({"lead_id": result.get("lead_id")}, {"_id": 0})
    if not lead or not lead.get("email"):
        raise HTTPException(status_code=404, detail="No contact on file for this result")

    scored = await scored_result(result)
    top = scored[0]
    subject = f"Your cardIQ match: {top['card']['name']}"
    html = _build_recommendation_email(lead.get("name", "there"), top["card"], top["reasons"])
    email_id = await send_email(to=lead["email"], subject=subject, html=html)
    await db.quiz_results.update_one({"result_id": result_id}, {"$set": {"email_sent": True}})
    return {"status": "success", "email_id": email_id, "sent_to": lead["email"]}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.dict())
    await db.status_checks.insert_one(status_obj.dict())
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**_clean(s)) for s in status_checks]


def _date_query(date_from: Optional[str], date_to: Optional[str]) -> dict:
    """Build a created_at mongo filter from YYYY-MM-DD strings (inclusive range, UTC)."""
    from datetime import timedelta
    cond = {}
    if date_from:
        try:
            cond["$gte"] = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    if date_to:
        try:
            end = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc) + timedelta(days=1)
            cond["$lt"] = end
        except ValueError:
            pass
    return {"created_at": cond} if cond else {}


@api_router.get("/admin/cards")
async def admin_cards(x_admin_token: Optional[str] = Header(None)):
    role = _require_admin(x_admin_token)
    cards = await db.cards.find({"$or": [CATALOG_QUERY, {"publicationStatus": {"$exists": True}}]}, {"_id": 0}).sort("name", 1).to_list(None)
    return {"cards": [_admin_card(card) for card in cards], "role": role}


@api_router.post("/admin/cards", status_code=201)
async def create_admin_card(payload: AdminCardIn, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "editor")
    base = re.sub(r"[^a-z0-9]+", "-", f"{payload.issuer}-{payload.name}".lower()).strip("-")[:80] or str(uuid.uuid4())
    card_id, suffix = base, 2
    while await db.cards.find_one({"id": card_id}, {"_id": 1}):
        card_id, suffix = f"{base}-{suffix}", suffix + 1
    draft = _admin_card_doc(payload, card_id)
    doc = {
        "id": card_id, "name": draft["name"], "issuer": draft["issuer"],
        "active": False, "applicationsOpen": False, "adminManaged": True,
        "publicationStatus": "draft", "draft": draft,
    }
    await db.cards.insert_one(doc)
    return _admin_card(doc)


@api_router.put("/admin/cards/{card_id}")
async def update_admin_card(card_id: str, payload: AdminCardIn, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "editor")
    existing = await db.cards.find_one({"id": card_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Card not found")
    doc = _admin_card_doc(payload, card_id, existing)
    await db.cards.update_one({"id": card_id}, {"$set": {"draft": doc}})
    updated = await db.cards.find_one({"id": card_id}, {"_id": 0})
    return _admin_card(updated)


@api_router.post("/admin/cards/{card_id}/publish")
async def publish_admin_card(card_id: str, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "publisher")
    card = await db.cards.find_one({"id": card_id}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    draft = card.get("draft")
    if not draft:
        raise HTTPException(status_code=409, detail="This card has no draft to publish")
    if card.get("publicationStatus") != "draft":
        snapshot = {key: value for key, value in card.items() if key not in {"_id", "draft"}}
        await db.card_versions.insert_one({
            "version_id": str(uuid.uuid4()), "card_id": card_id,
            "created_at": datetime.now(timezone.utc), "snapshot": snapshot,
        })
    draft.update({"id": card_id, "adminManaged": True, "publicationStatus": "published"})
    await db.cards.update_one({"id": card_id}, {"$set": draft, "$unset": {"draft": ""}})
    return _admin_card(await db.cards.find_one({"id": card_id}, {"_id": 0}))


@api_router.get("/admin/cards/{card_id}/history")
async def admin_card_history(card_id: str, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    versions = await db.card_versions.find({"card_id": card_id}, {"_id": 0, "snapshot": 0}).sort("created_at", -1).to_list(50)
    return {"versions": versions}


@api_router.post("/admin/cards/{card_id}/rollback/{version_id}")
async def rollback_admin_card(card_id: str, version_id: str, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "publisher")
    version = await db.card_versions.find_one({"card_id": card_id, "version_id": version_id}, {"_id": 0})
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    draft = version["snapshot"]
    draft["id"] = card_id
    await db.cards.update_one({"id": card_id}, {"$set": {"draft": draft}})
    return _admin_card(await db.cards.find_one({"id": card_id}, {"_id": 0}))


@api_router.post("/admin/cards/{card_id}/archive")
async def archive_admin_card(card_id: str, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "publisher")
    card = await db.cards.find_one({"id": card_id}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    snapshot = {key: value for key, value in card.items() if key not in {"_id", "draft"}}
    await db.card_versions.insert_one({"version_id": str(uuid.uuid4()), "card_id": card_id, "created_at": datetime.now(timezone.utc), "snapshot": snapshot})
    await db.cards.update_one({"id": card_id}, {"$set": {"active": False, "applicationsOpen": False, "publicationStatus": "archived", "adminManaged": True}, "$unset": {"draft": ""}})
    return _admin_card(await db.cards.find_one({"id": card_id}, {"_id": 0}))


@api_router.post("/admin/cards/{card_id}/restore")
async def restore_admin_card(card_id: str, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "publisher")
    result = await db.cards.update_one({"id": card_id, "publicationStatus": "archived"}, {"$set": {"active": True, "applicationsOpen": True, "publicationStatus": "published", "adminManaged": True}})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Archived card not found")
    return _admin_card(await db.cards.find_one({"id": card_id}, {"_id": 0}))


@api_router.delete("/admin/cards/{card_id}/draft")
async def discard_admin_card_draft(card_id: str, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "editor")
    card = await db.cards.find_one({"id": card_id}, {"_id": 0})
    if not card or not card.get("draft"):
        raise HTTPException(status_code=404, detail="Draft not found")
    if card.get("publicationStatus") == "draft":
        await db.cards.delete_one({"id": card_id})
        return {"deleted": True, "id": card_id}
    await db.cards.update_one({"id": card_id}, {"$unset": {"draft": ""}})
    return _admin_card(await db.cards.find_one({"id": card_id}, {"_id": 0}))


@api_router.post("/admin/cards/{card_id}/recommendation-preview")
async def preview_card_recommendation(card_id: str, payload: RecommendationPreviewIn, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    target = await db.cards.find_one({"id": card_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Card not found")
    candidate = target.get("draft") or target
    cards = await db.cards.find(RECOMMENDABLE_QUERY, {"_id": 0}).to_list(None)
    cards = [candidate if card["id"] == card_id else card for card in cards]
    if not any(card["id"] == card_id for card in cards):
        cards.append(candidate)
    scored = recommend_cards(payload.answers, cards)
    rank = next((index + 1 for index, item in enumerate(scored) if item["card"]["id"] == card_id), None)
    match = next((item for item in scored if item["card"]["id"] == card_id), None)
    return {"rank": rank, "total": len(scored), "confidence": match.get("confidence") if match else None, "reasons": match.get("reasons", []) if match else [], "top_card": scored[0]["card"]["name"] if scored else None}


@api_router.get("/admin/cards-export")
async def export_admin_cards(format: str = "json", x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    cards = await db.cards.find(CATALOG_QUERY, {"_id": 0, "draft": 0}).sort("issuer", 1).to_list(None)
    if format == "json":
        return {"cards": cards}
    if format != "csv":
        raise HTTPException(status_code=422, detail="Format must be json or csv")
    import csv, io
    fields = ["id", "name", "issuer", "variantName", "productGroupId", "network", "annualFee", "joiningFee", "rewardLine", "applyUrl", "verifiedOn", "active", "applicationsOpen"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    for card in cards:
        writer.writerow({key: card.get(key, "") for key in fields})
    return Response(content=buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=cardiq-cards.csv"})


@api_router.post("/admin/cards-import")
async def import_admin_cards(payload: List[AdminCardIn], dry_run: bool = True, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "editor")
    if len(payload) > 1000:
        raise HTTPException(status_code=422, detail="Import is limited to 1,000 cards")
    if dry_run:
        return {"valid": True, "cards": len(payload), "message": "Validation passed; import will create drafts only."}
    created = []
    for item in payload:
        base = re.sub(r"[^a-z0-9]+", "-", f"{item.issuer}-{item.name}".lower()).strip("-")[:80] or str(uuid.uuid4())
        card_id, suffix = base, 2
        while await db.cards.find_one({"id": card_id}, {"_id": 1}):
            card_id, suffix = f"{base}-{suffix}", suffix + 1
        draft = _admin_card_doc(item, card_id)
        await db.cards.insert_one({"id": card_id, "name": draft["name"], "issuer": draft["issuer"], "active": False, "applicationsOpen": False, "adminManaged": True, "publicationStatus": "draft", "draft": draft})
        created.append(card_id)
    return {"created": len(created), "ids": created}


@api_router.put("/admin/cards/{card_id}/apply-link")
async def update_admin_card_apply_link(
    card_id: str,
    payload: ApplyLinkIn,
    x_admin_token: Optional[str] = Header(None),
):
    _require_admin(x_admin_token, "editor")
    apply_url = _validated_apply_url(payload.apply_url)
    update = {"$set": {"applyUrlOverride": apply_url}} if apply_url else {"$unset": {"applyUrlOverride": ""}}
    result = await db.cards.update_one({"id": card_id, **CATALOG_QUERY}, update)
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Card not found")
    card = await db.cards.find_one({"id": card_id}, {"_id": 0})
    return {
        "id": card["id"],
        "official_apply_url": card.get("applyUrl"),
        "custom_apply_url": card.get("applyUrlOverride"),
        "effective_apply_url": card.get("applyUrlOverride") or card.get("applyUrl"),
    }



@api_router.get("/admin/leads")
async def admin_leads(date_from: Optional[str] = None, date_to: Optional[str] = None, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    q = _date_query(date_from, date_to)
    leads = await db.leads.find(q, {"_id": 0}).sort("created_at", -1).to_list(2000)
    results = await db.quiz_results.find({}, {"_id": 0}).to_list(5000)
    res_map = {r["result_id"]: r for r in results}
    cards = await db.cards.find({}, {"_id": 0}).to_list(None)
    card_map = {c["id"]: c for c in cards}

    out = []
    for l in leads:
        r = res_map.get(l.get("result_id"))
        card = card_map.get(r["recommended_card_id"]) if r else None
        out.append({
            "name": l.get("name"),
            "email": l.get("email"),
            "phone": l.get("phone"),
            "created_at": l.get("created_at"),
            "result_id": l.get("result_id"),
            "recommended_card": card["name"] if card else "\u2014",
            "email_sent": bool(r.get("email_sent")) if r else False,
        })
    return {"total": len(out), "leads": out}


@api_router.get("/admin/leads.csv")
async def admin_leads_csv(token: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, x_admin_token: Optional[str] = Header(None)):
    """CSV export. Accepts token via header OR ?token= (so a browser download link works)."""
    provided = x_admin_token or token
    _require_admin(provided)
    q = _date_query(date_from, date_to)
    leads = await db.leads.find(q, {"_id": 0}).sort("created_at", -1).to_list(5000)
    results = await db.quiz_results.find({}, {"_id": 0}).to_list(10000)
    res_map = {r["result_id"]: r for r in results}
    cards = await db.cards.find({}, {"_id": 0}).to_list(None)
    card_map = {c["id"]: c for c in cards}

    import csv
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Name", "Email", "Phone", "Recommended Card", "Email Sent", "Created At", "Result ID"])
    for l in leads:
        r = res_map.get(l.get("result_id"))
        card = card_map.get(r["recommended_card_id"]) if r else None
        created = l.get("created_at")
        writer.writerow([
            l.get("name", ""),
            l.get("email", ""),
            l.get("phone", "") or "",
            card["name"] if card else "",
            "yes" if (r and r.get("email_sent")) else "no",
            created.isoformat() if hasattr(created, "isoformat") else str(created or ""),
            l.get("result_id", ""),
        ])
    csv_data = buf.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cardiq-leads.csv"},
    )


@api_router.get("/admin/insights")
async def admin_insights(date_from: Optional[str] = None, date_to: Optional[str] = None, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    q = _date_query(date_from, date_to)
    results = await db.quiz_results.find(q, {"_id": 0}).to_list(10000)
    cards = await db.cards.find({}, {"_id": 0}).to_list(None)
    card_map = {c["id"]: c for c in cards}

    total = len(results)
    card_counts: Dict[str, int] = {}
    goal_counts: Dict[str, int] = {}
    emailed = 0

    goal_labels = {
        "travel": "Travel",
        "shopping": "Shopping & Food",
        "fuel": "Bills & Fuel",
        "cashback": "Flat Cashback",
    }

    for r in results:
        cid = r.get("recommended_card_id")
        if cid:
            name = card_map.get(cid, {}).get("name", cid)
            card_counts[name] = card_counts.get(name, 0) + 1
        goal = (r.get("answers") or {}).get("goal")
        if goal:
            label = goal_labels.get(goal, goal.title())
            goal_counts[label] = goal_counts.get(label, 0) + 1
        if r.get("email_sent"):
            emailed += 1

    def to_sorted(d):
        items = sorted(d.items(), key=lambda kv: kv[1], reverse=True)
        return [
            {"label": k, "count": v, "pct": round(v * 100 / total) if total else 0}
            for k, v in items
        ]

    incomplete = await db.partial_sessions.count_documents({"completed": {"$ne": True}})

    funnel_events = ["landing_view", "quiz_started", "result_viewed", "lead_submitted", "apply_clicked"]
    funnel = {}
    for event in funnel_events:
        funnel[event] = len(await db.product_events.distinct("session_id", {**q, "event": event}))

    return {
        "total_results": total,
        "emails_sent": emailed,
        "by_card": to_sorted(card_counts),
        "by_goal": to_sorted(goal_counts),
        "incomplete_sessions": incomplete,
        "funnel": funnel,
    }


class PartialIn(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    answers: Dict[str, str] = {}
    step: int = 0


@api_router.post("/quiz/partial")
async def save_partial(payload: PartialIn):
    """Record a started-but-unfinished quiz keyed by email (for reminder emails)."""
    now = datetime.now(timezone.utc)
    await db.partial_sessions.update_one(
        {"email": payload.email},
        {
            "$set": {
                "email": payload.email,
                "name": payload.name,
                "answers": payload.answers,
                "step": payload.step,
                "completed": False,
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now, "reminder_sent": False},
        },
        upsert=True,
    )
    return {"status": "saved"}


def _build_reminder_email(name: str) -> str:
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:#f6f7f5;padding:24px"><tr><td align="center">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="max-width:520px;background:#ffffff;border-radius:16px;overflow:hidden;'
        f'font-family:Arial,Helvetica,sans-serif">'
        f'<tr><td style="background:#0d9488;padding:20px 24px">'
        f'<span style="color:#ffffff;font-size:20px;font-weight:800">card'
        f'<span style="color:#5eead4">IQ</span></span></td></tr>'
        f'<tr><td style="padding:24px">'
        f'<h1 style="margin:0 0 8px;color:#0f1a17;font-size:22px">You are one step away, {escape(name)}!</h1>'
        f'<p style="margin:0 0 12px;color:#55615c;font-size:14px">You started finding your perfect credit '
        f'card with cardIQ but did not finish. It only takes about 60 seconds, and your answers are saved.</p>'
        f'<p style="margin:0 0 12px;color:#55615c;font-size:14px">Come back any time to reveal your single, '
        f'unbiased recommendation.</p>'
        f'<p style="margin:18px 0 0;color:#888;font-size:12px">Sent by cardIQ. We never ask for your password '
        f'or card details by email.</p>'
        f'</td></tr></table></td></tr></table>'
    )


@api_router.post("/admin/send-reminders")
async def send_reminders(x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "editor")
    pending = await db.partial_sessions.find(
        {"completed": {"$ne": True}, "reminder_sent": {"$ne": True}}, {"_id": 0}
    ).to_list(1000)
    sent = 0
    for p in pending:
        try:
            html = _build_reminder_email(p.get("name") or "there")
            await send_email(to=p["email"], subject="Finish finding your cardIQ match", html=html)
            await db.partial_sessions.update_one(
                {"email": p["email"]}, {"$set": {"reminder_sent": True}}
            )
            sent += 1
        except Exception as e:
            logger.error(f"Reminder email failed for {p.get('email')}: {e}")
    return {"status": "success", "reminders_sent": sent, "pending": len(pending)}


@api_router.get("/admin/card-reviews")
async def admin_card_reviews(x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    reviews = await db.cardholder_reviews.find({}, {"_id": 0}).sort("created_at", -1).to_list(2000)
    cards = await db.cards.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(None)
    names = {card["id"]: card["name"] for card in cards}
    for review in reviews:
        review["card_name"] = names.get(review["card_id"], review["card_id"])
    return {"reviews": reviews}


@api_router.put("/admin/card-reviews/{review_id}")
async def moderate_card_review(review_id: str, payload: ReviewModerationIn, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "publisher")
    if payload.status not in {"approved", "rejected"}:
        raise HTTPException(status_code=422, detail="Status must be approved or rejected")
    result = await db.cardholder_reviews.update_one({"review_id": review_id}, {"$set": {"status": payload.status, "moderated_at": datetime.now(timezone.utc)}})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"status": payload.status}


@api_router.post("/admin/send-review-reminders")
async def send_review_reminders(x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "editor")
    now = datetime.now(timezone.utc)
    due = await db.review_followups.find({"due_at": {"$lte": now}, "reminder_sent": False, "review_submitted": False, "review_consent": True}, {"_id": 0}).to_list(1000)
    cards = await db.cards.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(None)
    names = {card["id"]: card["name"] for card in cards}
    sent = 0
    for followup in due:
        token = secrets.token_urlsafe(32)
        url = f"{PUBLIC_APP_URL}/review/{token}"
        card_name = names.get(followup["card_id"], "your card")
        html = (f'<table role="presentation" width="100%" style="font-family:Arial,sans-serif;background:#f6f7f5;padding:24px"><tr><td>'
                f'<h1 style="color:#0f1a17;font-size:22px">How is {escape(card_name)} working for you?</h1>'
                f'<p style="color:#55615c">Your experience can help other customers make a better decision. This link can be used once.</p>'
                f'<a href="{url}" style="display:inline-block;background:#0d9488;color:#fff;padding:12px 18px;border-radius:10px;text-decoration:none">Review this card</a>'
                f'<p style="color:#888;font-size:12px">This is the one review reminder you requested. It is not a marketing subscription.</p></td></tr></table>')
        try:
            await send_email(to=followup["email"], subject=f"Review your {card_name}", html=html)
            await db.review_followups.update_one({"followup_id": followup["followup_id"]}, {"$set": {"reminder_sent": True, "reminder_sent_at": now, "token_hash": hashlib.sha256(token.encode()).hexdigest(), "token_expires_at": now + timedelta(days=30)}})
            sent += 1
        except Exception as exc:
            logger.error(f"Review reminder failed for followup {followup['followup_id']}: {exc}")
    return {"due": len(due), "sent": sent}



app.include_router(api_router)

cors_origins = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if origin.strip()]
allow_all_origins = "*" in cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_credentials=not allow_all_origins,
    allow_origins=["*"] if allow_all_origins else cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@app.on_event("startup")
async def on_startup():
    await seed_cards(db)
    await db.product_events.create_index(
        [("event", 1), ("session_id", 1), ("result_id", 1)],
        unique=True,
        name="unique_product_funnel_event",
    )
    await db.product_events.create_index("created_at", name="product_event_created_at")
    logger.info("cardIQ card catalog seeded")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
