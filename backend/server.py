from fastapi import FastAPI, APIRouter, HTTPException, Header, Response, Request, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
import os
import re
import ipaddress
import logging
import httpx
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Dict, Optional, Any
import uuid
import secrets
import asyncio
import hashlib
import unicodedata
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

from cards_seed import CARDS, seed_cards, recommend_cards, card_economics_profile, CATALOG_QUERY, RECOMMENDABLE_QUERY
from card_images import normalize_card_image, validate_card_image_url, MAX_IMAGE_BYTES
from restricted_access import restricted_access
from email_transport import deliver_email, EmailConfigurationError, EmailDeliveryError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
USE_IN_MEMORY_DB = os.environ.get("USE_IN_MEMORY_DB", "false").lower() in {"1", "true", "yes"}
if USE_IN_MEMORY_DB:
    from mongomock_motor import AsyncMongoMockClient
    client = AsyncMongoMockClient()
else:
    client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]
_link_monitor_task = None


async def _ensure_product_event_index():
    keys = [("event", 1), ("session_id", 1), ("result_id", 1), ("card_id", 1), ("channel", 1), ("page_type", 1), ("experiment_id", 1), ("variant", 1)]
    name = "unique_product_funnel_event"
    existing = (await db.product_events.index_information()).get(name)
    # Keep the unique index in place during ordinary restarts. Only the legacy
    # schema requires migration; rebuilding on every boot opens a duplicate race.
    if existing and (list(existing.get("key", [])) != keys or not existing.get("unique")):
        await db.product_events.drop_index(name)
    await db.product_events.create_index(keys, unique=True, name=name)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize database state and background work using FastAPI's lifespan API."""
    global _link_monitor_task
    await seed_cards(db)
    await _ensure_product_event_index()
    await db.product_events.create_index("created_at", name="product_event_created_at")
    await db.partner_conversions.create_index("external_id", unique=True, name="unique_partner_conversion")
    await db.partner_conversions.create_index("created_at", name="partner_conversion_created_at")
    await db.apply_link_checks.create_index([("card_id", 1), ("checked_at", -1)], name="apply_link_check_card_date")
    if os.environ.get("ENABLE_APPLY_LINK_MONITOR", "true").lower() == "true":
        _link_monitor_task = asyncio.create_task(_link_monitor_loop())
    logger.info("cardIQ card catalog seeded")
    try:
        yield
    finally:
        if _link_monitor_task:
            _link_monitor_task.cancel()
            try:
                await _link_monitor_task
            except asyncio.CancelledError:
                pass
            _link_monitor_task = None
        client.close()


app = FastAPI(title="cardIQ API", version="1.0.0", lifespan=lifespan)
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

# ---------------- Email (direct provider transport) ----------------
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
    try:
        return await deliver_email(to=to, subject=subject, html=html, reply_to=reply_to)
    except EmailConfigurationError:
        raise HTTPException(status_code=503, detail="Email service is not configured")
    except EmailDeliveryError:
        logger.error("Email provider delivery failed")
        raise HTTPException(status_code=502, detail="Failed to send email")


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


class ValueCalculatorIn(BaseModel):
    online: int = Field(default=0, ge=0, le=2_000_000)
    dining: int = Field(default=0, ge=0, le=2_000_000)
    travel: int = Field(default=0, ge=0, le=2_000_000)
    fuel: int = Field(default=0, ge=0, le=2_000_000)
    international: int = Field(default=0, ge=0, le=2_000_000)
    other: int = Field(default=0, ge=0, le=2_000_000)
    lounge_visits: int = Field(default=0, ge=0, le=100)
    fee_preference: str = "worth"

    @field_validator("fee_preference")
    @classmethod
    def validate_fee_preference(cls, value: str) -> str:
        if value not in {"free", "worth", "premium"}:
            raise ValueError("Unsupported fee preference")
        return value


class PurchaseOptimizerIn(BaseModel):
    card_ids: List[str] = Field(min_length=1, max_length=10)
    category: str
    amount: int = Field(ge=1, le=10_000_000)

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        if value not in {"online", "dining", "travel", "fuel", "grocery", "international", "upi", "other"}:
            raise ValueError("Unsupported purchase category")
        return value


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


class CardAlertSubscriptionIn(BaseModel):
    email: EmailStr
    scope_type: str
    scope_value: Optional[str] = None
    alert_consent: bool

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, value: str) -> str:
        if value not in {"all", "issuer", "card"}:
            raise ValueError("Unsupported alert scope")
        return value


class CardAlertUnsubscribeIn(BaseModel):
    token: str = Field(min_length=32, max_length=200)


class AdminCardAlertSendIn(BaseModel):
    card_id: str
    title: str = Field(min_length=5, max_length=120)
    summary: str = Field(min_length=20, max_length=1000)
    source_url: str
    idempotency_key: str = Field(min_length=8, max_length=120, pattern=r"^[a-zA-Z0-9._-]+$")
    change_type: str
    effective_date: Optional[str] = None

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str) -> str:
        if not value.startswith("https://") or not _host_ok(urlparse(value).hostname or ""):
            raise ValueError("Use a safe HTTPS issuer source")
        return value

    @field_validator("change_type")
    @classmethod
    def validate_change_type(cls, value: str) -> str:
        if value not in {"launch", "fee-change", "reward-change", "devaluation", "benefit-change", "discontinued"}:
            raise ValueError("Unsupported card update type")
        return value

    @field_validator("effective_date")
    @classmethod
    def validate_effective_date(cls, value: Optional[str]) -> Optional[str]:
        if value and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("Effective date must use YYYY-MM-DD")
        return value


class ProductEventIn(BaseModel):
    event: str
    session_id: str
    result_id: Optional[str] = None
    card_id: Optional[str] = None
    channel: Optional[str] = None
    page_type: Optional[str] = None
    experiment_id: Optional[str] = None
    variant: Optional[str] = None

    @field_validator("event")
    @classmethod
    def validate_event(cls, value: str) -> str:
        allowed = {"landing_view", "quiz_started", "result_viewed", "lead_submitted", "apply_clicked", "content_shared", "calculator_completed"}
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

    @field_validator("experiment_id", "variant")
    @classmethod
    def validate_experiment_dimension(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not re.fullmatch(r"[a-z0-9_-]{1,80}", value):
            raise ValueError("Invalid experiment dimension")
        return value


class SiteLinkIn(BaseModel):
    label: str = Field(min_length=1, max_length=60)
    url: str = Field(min_length=1, max_length=500)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if value.startswith("/") or (value.startswith("https://") and _host_ok(urlparse(value).hostname or "")):
            return value
        raise ValueError("Footer links must use an internal path or safe HTTPS URL")


class FooterGroupIn(BaseModel):
    title: str = Field(min_length=1, max_length=60)
    links: List[SiteLinkIn] = Field(min_length=1, max_length=12)


class FeaturedPlacementIn(BaseModel):
    card_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,119}$")
    placement_type: str
    label: str = Field(min_length=1, max_length=40)
    summary: Optional[str] = Field(default=None, max_length=300)
    active: bool = True

    @field_validator("placement_type")
    @classmethod
    def validate_placement_type(cls, value: str) -> str:
        if value not in {"launch", "partner"}:
            raise ValueError("Placement type must be launch or partner")
        return value


class SiteContentIn(BaseModel):
    footer_groups: List[FooterGroupIn] = Field(min_length=1, max_length=8)
    featured_cards: List[FeaturedPlacementIn] = Field(default_factory=list, max_length=4)


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
    partner_name: Optional[str] = None
    campaign_id: Optional[str] = None
    tracking_id: Optional[str] = None
    status: str = "live"
    expected_payout: Optional[float] = None


class ReconciliationRowIn(BaseModel):
    external_id: str = Field(min_length=3, max_length=160, pattern=r"^[A-Za-z0-9._-]+$")
    status: str
    commission: float = Field(default=0, ge=0, le=10_000_000)
    card_id: Optional[str] = None
    campaign_id: Optional[str] = None
    tracking_id: Optional[str] = None
    occurred_at: Optional[datetime] = None

    @field_validator("status")
    @classmethod
    def validate_conversion_status(cls, value: str) -> str:
        if value not in {"applied", "approved", "rejected", "reversed", "paid"}:
            raise ValueError("Unsupported reconciliation status")
        return value


class EditorialAlternativeIn(BaseModel):
    id: str
    name: str
    reason: str


class EditorialContentIn(BaseModel):
    summary: str
    idealFor: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    verdict: str
    alternatives: List[EditorialAlternativeIn] = Field(default_factory=list)


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
    editorial: Optional[EditorialContentIn] = None
    editorialReviewed: bool = False
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
    public = {key: value for key, value in card.items() if key not in {"_id", "draft", "adminManaged", "publicationStatus", "applyLinkPausedReason"}}
    override = public.pop("applyUrlOverride", None)
    status = public.pop("applyLinkStatus", "live" if override else "official")
    public["officialApplyUrl"] = public.get("applyUrl")
    if override and status == "live":
        public["applyUrl"] = override
        public["applicationLinkType"] = "partner"
    else:
        public["applicationLinkType"] = "official"
    public["affiliateDisclosureRequired"] = public["applicationLinkType"] == "partner"
    public["economicsProfile"] = card_economics_profile(public)
    for key in ("applyPartner", "applyCampaignId", "applyTrackingId", "expectedPayout", "applyLinkUpdatedAt"):
        public.pop(key, None)
    return public


CARD_SUMMARY_FIELDS = {
    "id", "name", "issuer", "tagline", "network", "palette", "accent", "annualFee",
    "annualFeeAmount", "joiningFee", "joiningFeeAmount", "rewardLine", "bestFor", "feeType",
    "minSpend", "creditReq", "rating", "verifiedOn", "applicationsOpen", "secured", "active",
    "coBrandPartner", "imageUrl", "editorial", "recommendationEligible",
    "applyUrl", "officialApplyUrl", "applicationLinkType", "affiliateDisclosureRequired",
    "homepagePlacement", "lifetimeFree",
}
CARD_SUMMARY_SOURCE_FIELDS = CARD_SUMMARY_FIELDS | {
    "applyUrlOverride", "applyLinkStatus", "applyPartner", "applyCampaignId", "applyTrackingId",
    "expectedPayout", "applyLinkUpdatedAt",
}
PUBLIC_RECOMMENDATION_LIMIT = 3
RESULT_READ_PROJECTION = {
    "_id": 0,
    "result_id": 1,
    "answers": 1,
    "lead_id": 1,
    "scored": {"$slice": PUBLIC_RECOMMENDATION_LIMIT},
    "scored_ids": {"$slice": PUBLIC_RECOMMENDATION_LIMIT},
}


def _card_summary_for_client(card: dict) -> dict:
    """Return fields needed to search and render catalogue tiles, not full card detail."""
    public = _card_for_client(card)
    summary = {key: public[key] for key in CARD_SUMMARY_FIELDS if key in public}
    editorial = summary.get("editorial")
    if editorial:
        summary["editorial"] = {"summary": editorial["summary"]} if editorial.get("summary") else {}
    return summary


def _require_admin(token: Optional[str], minimum: str = "viewer") -> str:
    roles = {ADMIN_VIEWER_TOKEN: "viewer", ADMIN_EDITOR_TOKEN: "editor", ADMIN_PUBLISHER_TOKEN: "publisher", ADMIN_TOKEN: "owner"}
    roles = {secret: role for secret, role in roles.items() if secret}
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


def _apply_link_update(payload: ApplyLinkIn) -> dict:
    """Validate partner-link configuration and return the Mongo update document."""
    apply_url = _validated_apply_url(payload.apply_url)
    if payload.status not in {"testing", "live", "paused"}:
        raise HTTPException(status_code=422, detail="Partner link status must be testing, live or paused")
    partner_name = (payload.partner_name or "").strip() or None
    campaign_id = (payload.campaign_id or "").strip() or None
    tracking_id = (payload.tracking_id or "").strip() or None
    if apply_url and payload.status == "live" and not partner_name:
        raise HTTPException(status_code=422, detail="Partner name is required before a link goes live")
    if payload.expected_payout is not None and payload.expected_payout < 0:
        raise HTTPException(status_code=422, detail="Expected payout cannot be negative")
    if apply_url:
        return {"$set": {
            "applyUrlOverride": apply_url, "applyPartner": partner_name,
            "applyCampaignId": campaign_id, "applyTrackingId": tracking_id,
            "applyLinkStatus": payload.status, "expectedPayout": payload.expected_payout,
            "applyLinkUpdatedAt": datetime.now(timezone.utc),
        }}
    return {"$unset": {key: "" for key in (
        "applyUrlOverride", "applyPartner", "applyCampaignId", "applyTrackingId",
        "applyLinkStatus", "expectedPayout", "applyLinkUpdatedAt",
    )}}


def _admin_card_doc(payload: AdminCardIn, card_id: str, existing: Optional[dict] = None) -> dict:
    values = payload.model_dump()
    editorial_reviewed = values.pop("editorialReviewed", False)
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
    try:
        values["imageUrl"] = validate_card_image_url(values.get("imageUrl"))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    values["name"], values["issuer"] = name, issuer
    values["variants"] = list(dict.fromkeys(v.strip() for v in values["variants"] if v.strip()))
    for list_field in ("highlights", "welcomeBenefits", "milestoneBenefits", "loungeBenefits", "exclusions"):
        values[list_field] = [v.strip() for v in values[list_field] if v.strip()]
    values["bestFor"] = list(dict.fromkeys(v.strip().lower() for v in values["bestFor"] if v.strip()))
    values["sourceUrls"] = list(dict.fromkeys(filter(None, [_validated_apply_url(v) for v in values["sourceUrls"]])))
    for text_field in ("rewardCurrency", "rewardRedemption", "forexMarkup", "fuelBenefits", "eligibilityNote"):
        values[text_field] = (values.get(text_field) or "").strip() or None
    if values.get("editorial"):
        editorial = values["editorial"]
        editorial["summary"] = editorial["summary"].strip()
        editorial["verdict"] = editorial["verdict"].strip()
        for field in ("idealFor", "strengths", "tradeoffs"):
            editorial[field] = [item.strip() for item in editorial[field] if item.strip()]
        editorial["alternatives"] = [
            {key: item[key].strip() for key in ("id", "name", "reason")}
            for item in editorial["alternatives"] if all(item.get(key, "").strip() for key in ("id", "name", "reason"))
        ][:3]
        if not editorial["summary"] or not editorial["verdict"]:
            raise HTTPException(status_code=422, detail="Editorial summary and verdict are required")
    editorial_scalar_fields = (
        "name", "issuer", "annualFee", "annualFeeAmount", "joiningFee", "joiningFeeAmount",
        "rewardLine", "rewardCurrency", "rewardRedemption", "forexMarkup", "fuelBenefits",
        "eligibilityNote", "applicationsOpen",
    )
    editorial_list_fields = ("highlights", "welcomeBenefits", "milestoneBenefits", "loungeBenefits", "exclusions", "bestFor")
    facts_changed = existing and (
        any((existing.get(field) or None) != (values.get(field) or None) for field in editorial_scalar_fields)
        or any((existing.get(field) or []) != (values.get(field) or []) for field in editorial_list_fields)
    )
    if facts_changed and existing.get("editorial"):
        if existing.get("editorial") == values.get("editorial") and not editorial_reviewed:
            raise HTTPException(status_code=422, detail="Card facts changed. Review the editorial and confirm it before saving the draft")
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
        "effective_apply_url": public.get("applyUrlOverride") if public.get("applyUrlOverride") and public.get("applyLinkStatus", "live") == "live" else public.get("applyUrl"),
        "partner_name": public.get("applyPartner"),
        "campaign_id": public.get("applyCampaignId"),
        "tracking_id": public.get("applyTrackingId"),
        "apply_link_status": public.get("applyLinkStatus", "live" if public.get("applyUrlOverride") else "official"),
        "expected_payout": public.get("expectedPayout"),
        "has_draft": bool(draft),
        "publication_status": "draft" if draft else stored.get("publicationStatus", "published"),
        "is_new_draft": bool(draft and stored.get("publicationStatus") == "draft"),
        "draft": draft,
        "economicsProfile": card_economics_profile(public),
    })
    return public


# ---------------- Routes ----------------
@api_router.get("/")
async def root():
    return {"message": "cardIQ API"}


@api_router.get("/ready")
async def readiness(response: Response):
    response.headers["Cache-Control"] = "no-store"
    try:
        await asyncio.wait_for(db.command("ping"), timeout=2)
        available = await asyncio.wait_for(db.cards.find_one(RECOMMENDABLE_QUERY, {"_id": 1}), timeout=2)
        if not available:
            raise RuntimeError("Catalogue unavailable")
    except Exception:
        raise HTTPException(status_code=503, detail="Service unavailable", headers={"Cache-Control": "no-store"}) from None
    return {"status": "ready"}


@api_router.get("/cards")
async def get_cards(view: str = "full"):
    if view == "summary":
        projection = {key: 1 for key in CARD_SUMMARY_SOURCE_FIELDS}
        projection["_id"] = 0
        cards = await db.cards.find(CATALOG_QUERY, projection).to_list(None)
        return [_card_summary_for_client(card) for card in cards]
    if view != "full":
        raise HTTPException(status_code=422, detail="view must be full or summary")
    cards = await db.cards.find(CATALOG_QUERY, {"_id": 0}).to_list(None)
    return [_card_for_client(card) for card in cards]


@api_router.get("/restricted-cards")
async def get_restricted_cards():
    cards = await db.cards.find(CATALOG_QUERY, {"_id": 0}).to_list(None)
    results = []
    for card in cards:
        access = restricted_access(card)
        if access:
            results.append({**_card_for_client(card), **access, "recommendationExcluded": True})
    return {"cards": sorted(results, key=lambda item: (item["accessType"], item["issuer"], item["name"]))}


COMPARISON_PLACEMENTS = {"verdict_box_card_a", "verdict_box_card_b", "calculator_winner_cta", "sticky_mobile_bar", "fallback_footer_ltf", "list_card", "unattributed"}


@api_router.get("/go/{card_id}")
async def comparison_apply_redirect(card_id: str, subid: str = Query("unattributed", max_length=40), pair: Optional[str] = Query(None, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"), source: Optional[str] = Query(None, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")):
    if subid not in COMPARISON_PLACEMENTS:
        raise HTTPException(status_code=422, detail="Unknown comparison placement")
    card = await db.cards.find_one({"id": card_id, **CATALOG_QUERY}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if card.get("active") is False or card.get("applicationsOpen") is False:
        raise HTTPException(status_code=409, detail="Applications are not currently confirmed open. Check the issuer's current availability.")
    partner = bool(card.get("applyUrlOverride") and card.get("applyLinkStatus", "live") == "live")
    destination = _validated_apply_url(card.get("applyUrlOverride") if partner else card.get("applyUrl"))
    if not destination:
        raise HTTPException(status_code=503, detail="Issuer destination unavailable")
    if partner:
        parsed = urlparse(destination)
        params = parse_qsl(parsed.query, keep_blank_values=True)
        keys = {key for key, _ in params}
        # Preserve existing network/campaign attribution instead of overwriting partner parameters.
        params.append(("cardiq_subid" if "subid" in keys else "subid", subid))
        if pair: params.append(("cardiq_pair" if "pair" in keys else "pair", pair))
        if source: params.append(("cardiq_source" if "source" in keys else "source", source))
        destination = urlunparse(parsed._replace(query=urlencode(params)))
    await db.apply_events.insert_one({
        "event_id": str(uuid.uuid4()), "card_id": card_id, "result_id": None,
        "link_type": "partner" if partner else "official", "placement_id": subid,
        "comparison_slug": pair, "source_page": source, "partner_name": card.get("applyPartner") if partner else None,
        "campaign_id": card.get("applyCampaignId") if partner else None,
        "tracking_id": card.get("applyTrackingId") if partner else None,
        "destination_url": destination, "expected_payout": card.get("expectedPayout") if partner else None,
        "created_at": datetime.now(timezone.utc),
    })
    return RedirectResponse(destination, status_code=302, headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"})


@api_router.post("/cards/{card_id}/apply-click")
async def track_apply_click(card_id: str, payload: ApplyClickIn):
    card = await db.cards.find_one({"id": card_id, **CATALOG_QUERY}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    status = card.get("applyLinkStatus", "live" if card.get("applyUrlOverride") else "official")
    partner_live = bool(card.get("applyUrlOverride") and status == "live")
    await db.apply_events.insert_one({
        "event_id": str(uuid.uuid4()), "card_id": card_id, "result_id": payload.result_id,
        "link_type": "partner" if partner_live else "official",
        "partner_name": card.get("applyPartner") if partner_live else None,
        "campaign_id": card.get("applyCampaignId") if partner_live else None,
        "tracking_id": card.get("applyTrackingId") if partner_live else None,
        "destination_url": card.get("applyUrlOverride") if partner_live else card.get("applyUrl"),
        "expected_payout": card.get("expectedPayout") if partner_live else None,
        "created_at": datetime.now(timezone.utc),
    })
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


@api_router.post("/card-alerts", status_code=201)
async def subscribe_card_alerts(payload: CardAlertSubscriptionIn):
    if not payload.alert_consent:
        raise HTTPException(status_code=422, detail="Card-alert consent is required")
    scope_value = (payload.scope_value or "").strip()
    if payload.scope_type != "all" and not scope_value:
        raise HTTPException(status_code=422, detail="Choose what you want to follow")
    if payload.scope_type == "card" and not await db.cards.find_one({"id": scope_value, **CATALOG_QUERY}, {"_id": 1}):
        raise HTTPException(status_code=404, detail="Card not found")
    if payload.scope_type == "issuer" and not await db.cards.find_one({"issuer": scope_value, **CATALOG_QUERY}, {"_id": 1}):
        raise HTTPException(status_code=404, detail="Issuer not found")
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    email = str(payload.email).lower()
    await db.card_alert_subscriptions.update_one(
        {"email": email, "scope_type": payload.scope_type, "scope_value": scope_value or None},
        {"$set": {"status": "active", "alert_consent": True, "marketing_consent": False,
                  "updated_at": now, "unsubscribe_token_hash": hashlib.sha256(token.encode()).hexdigest()},
         "$setOnInsert": {"subscription_id": str(uuid.uuid4()), "email": email,
                          "scope_type": payload.scope_type, "scope_value": scope_value or None, "created_at": now}},
        upsert=True,
    )
    return {"status": "subscribed", "unsubscribeToken": token}


@api_router.post("/card-alerts/unsubscribe")
async def unsubscribe_card_alerts(payload: CardAlertUnsubscribeIn):
    result = await db.card_alert_subscriptions.update_one(
        {"$or": [{"unsubscribe_token_hash": hashlib.sha256(payload.token.encode()).hexdigest()},
                  {"unsubscribe_token_hashes": hashlib.sha256(payload.token.encode()).hexdigest()}], "status": "active"},
        {"$set": {"status": "unsubscribed", "unsubscribed_at": datetime.now(timezone.utc)}},
    )
    if not result.modified_count:
        raise HTTPException(status_code=404, detail="Subscription not found or already inactive")
    return {"status": "unsubscribed"}


@api_router.post("/admin/card-alerts/send")
async def send_card_change_alert(payload: AdminCardAlertSendIn, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "publisher")
    card = await db.cards.find_one({"id": payload.card_id, **CATALOG_QUERY}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    allowed_sources = set(card.get("sourceUrls") or []) | {card.get("officialApplyUrl"), card.get("applyUrl")}
    if payload.source_url not in allowed_sources:
        raise HTTPException(status_code=422, detail="Source URL must already be a verified source for this card")
    existing = await db.card_alert_campaigns.find_one({"idempotency_key": payload.idempotency_key}, {"_id": 0})
    if existing:
        return {"status": "in_progress" if existing.get("delivery_state") == "sending" else "already_sent",
                "sent": existing.get("sent", 0), "failed": existing.get("failed", 0)}
    # MongoDB's built-in unique _id atomically reserves this campaign even when
    # multiple workers receive the same request at the same time.
    campaign_id = "card-alert:" + payload.idempotency_key
    try:
        await db.card_alert_campaigns.insert_one({"_id": campaign_id,
            "campaign_id": str(uuid.uuid4()), "idempotency_key": payload.idempotency_key,
            "delivery_state": "sending", "sent": 0, "failed": 0,
            "created_at": datetime.now(timezone.utc)})
    except DuplicateKeyError:
        return {"status": "in_progress", "sent": 0, "failed": 0}
    query = {"status": "active", "$or": [
        {"scope_type": "all"}, {"scope_type": "card", "scope_value": card["id"]},
        {"scope_type": "issuer", "scope_value": card["issuer"]},
    ]}
    subscriptions = await db.card_alert_subscriptions.find(query, {"_id": 0}).to_list(2000)
    sent = failed = 0
    for subscription in subscriptions:
        token = secrets.token_urlsafe(32)
        unsubscribe_url = f'{PUBLIC_APP_URL}/#/alerts/unsubscribe?token={token}'
        message = (f'<h1>{escape(payload.title)}</h1><p>{escape(payload.summary)}</p>'
                   f'<p><a href="{escape(payload.source_url)}">Check the issuer source</a></p>'
                   f'<p style="font-size:12px;color:#667">You received this service alert because you asked CardIQ to track {escape(card["name"])} or {escape(card["issuer"])}. '
                   f'<a href="{escape(unsubscribe_url)}">Unsubscribe</a>. CardIQ will never ask for sensitive banking credentials.</p>')
        try:
            # Keep prior email links valid, and persist the new link before send.
            hashes = [hashlib.sha256(token.encode()).hexdigest()]
            if subscription.get("unsubscribe_token_hash"):
                hashes.append(subscription["unsubscribe_token_hash"])
            await db.card_alert_subscriptions.update_one(
                {"subscription_id": subscription["subscription_id"]},
                {"$addToSet": {"unsubscribe_token_hashes": {"$each": hashes}}})
            await send_email(to=subscription["email"], subject=f'Card update: {payload.title}', html=message)
            sent += 1
            await db.card_alert_subscriptions.update_one({"subscription_id": subscription["subscription_id"]}, {"$set": {
                "unsubscribe_token_hash": hashlib.sha256(token.encode()).hexdigest(), "last_alert_at": datetime.now(timezone.utc)}})
        except Exception as error:
            failed += 1
            logger.error("Card alert delivery failed for subscription %s: %s", subscription.get("subscription_id"), error)
    await db.card_alert_campaigns.update_one({"_id": campaign_id}, {"$set": {"delivery_state": "finished",
        "card_id": card["id"], "issuer": card["issuer"], "title": payload.title, "summary": payload.summary,
        "card_name": card["name"], "change_type": payload.change_type, "effective_date": payload.effective_date,
        "source_url": payload.source_url, "matched": len(subscriptions), "sent": sent, "failed": failed,
        "completed_at": datetime.now(timezone.utc)}})
    return {"status": "sent", "matched": len(subscriptions), "sent": sent, "failed": failed}


@api_router.get("/card-updates")
async def public_card_updates(limit: int = 50):
    limit = max(1, min(limit, 100))
    campaigns = await db.card_alert_campaigns.find({}, {"_id": 0, "idempotency_key": 0, "matched": 0, "sent": 0, "failed": 0}).sort("created_at", -1).to_list(limit)
    published_launches = {(item.get("card_id"), item.get("change_type")) for item in campaigns}
    launch_cards = await db.cards.find({
        **CATALOG_QUERY,
        "homepagePlacement.active": True,
        "homepagePlacement.type": "launch",
    }, {"_id": 0}).to_list(20)
    catalogue_updates = []
    for card in launch_cards:
        if (card.get("id"), "launch") in published_launches:
            continue
        placement = card.get("homepagePlacement") or {}
        sources = card.get("sourceUrls") or []
        source_url = sources[0] if sources else card.get("officialApplyUrl") or card.get("applyUrl")
        if not source_url:
            continue
        catalogue_updates.append({
            "campaign_id": f'catalogue-launch-{card["id"]}',
            "card_id": card["id"],
            "issuer": card.get("issuer"),
            "card_name": card.get("name"),
            "change_type": "launch",
            "title": f'{card.get("name")} added to CardIQ',
            "summary": placement.get("summary") or card.get("tagline") or card.get("rewardLine"),
            "effective_date": None,
            "source_url": source_url,
            "created_at": card.get("verifiedOn"),
        })
    updates = campaigns + catalogue_updates
    updates.sort(key=lambda item: str(item.get("effective_date") or item.get("created_at") or ""), reverse=True)
    return {"updates": [_clean(item) for item in updates[:limit]]}


@api_router.post("/product-events", status_code=202)
async def record_product_event(payload: ProductEventIn):
    """Record a deduplicated, anonymous funnel event without arbitrary metadata."""
    now = datetime.now(timezone.utc)
    dimensions = {"event": payload.event, "session_id": payload.session_id, "result_id": payload.result_id,
                  "card_id": payload.card_id, "channel": payload.channel, "page_type": payload.page_type,
                  "experiment_id": payload.experiment_id, "variant": payload.variant}
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
            "experiment_id": payload.experiment_id,
            "variant": payload.variant,
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
    # Consume the invitation atomically before yielding to the review insert.
    invite = await db.review_followups.find_one_and_update(
        {"token_hash": token_hash, "review_submitted": False,
         "token_expires_at": {"$gt": datetime.now(timezone.utc)}},
        {"$set": {"review_submitted": True}})
    if not invite:
        raise HTTPException(status_code=404, detail="Review link is invalid or expired")
    review = payload.model_dump()
    review.update({"review_id": str(uuid.uuid4()), "card_id": invite["card_id"], "followup_id": invite["followup_id"],
                   "status": "pending", "created_at": datetime.now(timezone.utc)})
    try:
        await db.cardholder_reviews.insert_one(review)
    except Exception:
        # A database timeout may mean the insert succeeded. Keep the invitation
        # consumed so retries cannot create duplicate reviews.
        await db.review_followups.update_one(
            {"followup_id": invite["followup_id"], "token_hash": token_hash},
            {"$set": {"review_submission_state": "needs_review"}})
        raise HTTPException(status_code=503, detail="Review submission needs verification; please contact support") from None
    await db.review_followups.update_one(
        {"followup_id": invite["followup_id"], "token_hash": token_hash},
        {"$unset": {"token_hash": ""}})
    return {"status": "submitted_for_review"}


@api_router.get("/cards/{card_id}")
async def get_card(card_id: str):
    card = await db.cards.find_one({"id": card_id, "publicationStatus": {"$ne": "draft"}}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return _card_for_client(card)


@api_router.post("/cards/compare")
async def compare_cards(payload: CompareIn):
    if not payload.ids:
        raise HTTPException(status_code=400, detail="No card ids provided")
    cards = await db.cards.find({"id": {"$in": payload.ids}, "publicationStatus": {"$ne": "draft"}}, {"_id": 0}).to_list(20)
    order = {cid: i for i, cid in enumerate(payload.ids)}
    cards.sort(key=lambda c: order.get(c["id"], 999))
    return [_card_for_client(card) for card in cards]


@api_router.post("/tools/value-calculator")
async def calculate_card_value(payload: ValueCalculatorIn):
    spends = {
        "online": payload.online,
        "dining": payload.dining,
        "travel": payload.travel,
        "fuel": payload.fuel,
        "international": payload.international,
        "other": payload.other,
    }
    monthly_spend = sum(spends.values())
    if monthly_spend <= 0:
        raise HTTPException(status_code=422, detail="Enter at least one monthly spend amount")
    primary = max(spends, key=spends.get)
    goal = {"travel": "travel", "international": "travel", "fuel": "fuel", "online": "shopping"}.get(primary, "cashback")
    usage = {"travel": "flights", "international": "flights", "fuel": "fuel", "dining": "dining"}.get(primary, "online")
    priority = "forex" if payload.international == max(spends.values()) and payload.international else "lounge" if payload.travel == max(spends.values()) and payload.travel else "cashback" if primary in {"online", "other"} else "rewards"
    spend_band = "low" if monthly_spend < 20_000 else "mid" if monthly_spend < 50_000 else "high" if monthly_spend < 100_000 else "vhigh"
    answers = {
        "goal": goal,
        "usage": usage,
        "priority": priority,
        "fee": payload.fee_preference,
        "spend": spend_band,
        "creditRoute": "either",
        "monthlySpend": str(monthly_spend),
        "onlineSpend": str(payload.online),
        "diningSpend": str(payload.dining),
        "travelSpend": str(payload.travel),
        "fuelSpend": str(payload.fuel),
        "internationalSpend": str(payload.international),
        "loungeVisits": str(payload.lounge_visits),
    }
    cards = await db.cards.find(RECOMMENDABLE_QUERY, {"_id": 0}).to_list(None)
    if not cards:
        raise HTTPException(status_code=503, detail="Card catalog unavailable")
    scored = recommend_cards(answers, [_card_for_client(card) for card in cards])[:10]
    return {
        "monthlySpend": monthly_spend,
        "annualSpend": monthly_spend * 12,
        "assumptions": {
            "primaryCategory": primary,
            "feePreference": payload.fee_preference,
            "loungeVisitValue": 700,
            "model": "CardIQ editorial range",
        },
        "results": scored,
    }


@api_router.post("/tools/purchase-optimizer")
async def optimize_purchase(payload: PurchaseOptimizerIn):
    ids = list(dict.fromkeys(payload.card_ids))
    cards = await db.cards.find({"id": {"$in": ids}, **CATALOG_QUERY}, {"_id": 0}).to_list(10)
    if len(cards) != len(ids):
        raise HTTPException(status_code=404, detail="One or more selected cards are unavailable")
    category_tags = {
        "online": {"online", "shopping", "cashback"}, "dining": {"dining", "food"},
        "travel": {"travel", "flights", "hotels"}, "fuel": {"fuel"},
        "grocery": {"grocery", "shopping", "cashback"}, "international": {"forex", "travel"},
        "upi": {"upi", "rupay"}, "other": {"rewards", "cashback"},
    }
    keywords = category_tags[payload.category]
    ranked = []
    for stored in cards:
        card = _card_for_client(stored)
        best_for = set(card.get("bestFor") or [])
        matches = sorted(best_for & keywords)
        searchable = [card.get("rewardLine", ""), *(card.get("highlights") or [])]
        evidence = [line for line in searchable if any(word in line.lower() for word in keywords)][:3]
        economics = card["economicsProfile"]
        score = len(matches) * 30 + len(evidence) * 8 + economics["coverage"] / 10
        ranked.append({"card": card, "fitScore": round(score, 1), "categoryMatches": matches,
            "documentedEvidence": evidence or [card.get("rewardLine", "")], "economicsQuality": economics["quality"]})
    ranked.sort(key=lambda item: item["fitScore"], reverse=True)
    return {"category": payload.category, "amount": payload.amount, "results": ranked,
        "methodology": "Ranks only the cards you selected using documented category tags and sourced benefit text. It does not promise an exact reward because merchant coding, caps and exclusions can change the outcome."}


@api_router.post("/quiz/submit")
async def submit_quiz(payload: QuizSubmitIn):
    cards = await db.cards.find(RECOMMENDABLE_QUERY, {"_id": 0}).to_list(None)
    if not cards:
        raise HTTPException(status_code=503, detail="Card catalog unavailable")

    scored = recommend_cards(payload.answers, [_card_for_client(card) for card in cards])
    if not scored:
        raise HTTPException(status_code=503, detail="No cards currently available for application")
    scored = scored[:PUBLIC_RECOMMENDATION_LIMIT]
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
        snapshots = result["scored"][:PUBLIC_RECOMMENDATION_LIMIT]
        ids = [s["card"]["id"] for s in snapshots]
        current = await db.cards.find(
            {"id": {"$in": ids}}, {"_id": 0}
        ).to_list(None)
        current_by_id = {c["id"]: c for c in current}
        cards = []
        for item in snapshots:
            snapshot = dict(item["card"])
            latest = current_by_id.get(snapshot["id"])
            cards.append(_card_for_client(latest) if latest else snapshot)
        # Recalculate card-dependent scores, reasons and value estimates so a
        # corrected fee, benefit or availability is consistent on shared results
        # and in emails. Missing historical cards retain their saved snapshot.
        refreshed = recommend_cards(result["answers"], cards)
        # Preserve a readable historical result only when every former candidate
        # is now unavailable; the UI will clearly disable those application links.
        return (refreshed or recommend_cards(result["answers"], cards, include_unavailable=True))[:PUBLIC_RECOMMENDATION_LIMIT]
    # Older results store IDs only. Archived demo records remain available here.
    ids = (result.get("scored_ids") or [])[:PUBLIC_RECOMMENDATION_LIMIT]
    query = {"id": {"$in": ids}} if ids else RECOMMENDABLE_QUERY
    cards = await db.cards.find(query, {"_id": 0}).to_list(None)
    scored = recommend_cards(
        result["answers"], [_card_for_client(card) for card in cards],
        include_unavailable=bool(ids),
    )
    if not scored:
        raise HTTPException(status_code=410, detail="Cards for this result are no longer available")
    return scored[:PUBLIC_RECOMMENDATION_LIMIT]


@api_router.get("/results/{result_id}")
async def get_result(result_id: str):
    result = await db.quiz_results.find_one({"result_id": result_id}, RESULT_READ_PROJECTION)
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
    result = await db.quiz_results.find_one({"result_id": result_id}, RESULT_READ_PROJECTION)
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
    return {"status": "success", "email_id": email_id}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.model_dump())
    await db.status_checks.insert_one(status_obj.model_dump())
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**_clean(s)) for s in status_checks]


DEFAULT_FOOTER_GROUPS = [
    {"title": "Discover cards", "links": [{"label": "Browse all cards", "url": "/cards"}, {"label": "Card comparisons", "url": "/cards?mode=compare"}, {"label": "New and updated cards", "url": "/updates"}, {"label": "Invite-only cards", "url": "/restricted-cards"}]},
    {"title": "Tools", "links": [{"label": "Find my best card", "url": "/"}, {"label": "Annual value calculator", "url": "/calculator"}, {"label": "Which card should I use?", "url": "/wallet-optimizer"}, {"label": "Card change alerts", "url": "/alerts"}]},
    {"title": "Help & research", "links": [{"label": "Reviews and editorials", "url": "/guides/"}, {"label": "Issuer contacts", "url": "/help/issuers"}, {"label": "How to close a card", "url": "/help/issuers"}, {"label": "Credit card guides", "url": "/guides/"}]},
    {"title": "About CardIQ", "links": [{"label": "How recommendations work", "url": "/methodology/"}, {"label": "How CardIQ makes money", "url": "/methodology/"}, {"label": "Card catalogue", "url": "/catalog/"}]},
]
SITE_CONTENT_VERSION = 3


def _default_site_content() -> dict:
    placements = []
    for card in CARDS:
        placement = card.get("homepagePlacement") or {}
        if placement.get("active"):
            placements.append({"card_id": card["id"], "placement_type": placement.get("type", "launch"), "label": placement.get("label", "Featured card"), "summary": placement.get("summary"), "active": True})
    return {"schema_version": SITE_CONTENT_VERSION, "footer_groups": DEFAULT_FOOTER_GROUPS, "featured_cards": placements[:4]}


def _upgrade_site_content(content: dict) -> dict:
    if content.get("schema_version", 1) >= SITE_CONTENT_VERSION:
        return content
    upgraded = {**content, "schema_version": SITE_CONTENT_VERSION}
    upgraded["footer_groups"] = [
        {
            **group,
            "links": [
                ({**link, "label": "Find my best card"} if link.get("label") == "Find my card match"
                 else {**link, "label": "How CardIQ makes money"} if link.get("label") == "Affiliate disclosure"
                 else link)
                for link in group.get("links", [])
            ],
        }
        for group in content.get("footer_groups", [])
    ]
    return upgraded


async def _site_content() -> dict:
    stored = await db.site_content.find_one({"_id": "customer_site"}, {"_id": 0})
    if not stored:
        return _default_site_content()
    upgraded = _upgrade_site_content(stored)
    if upgraded != stored:
        await db.site_content.update_one({"_id": "customer_site"}, {"$set": upgraded})
    return upgraded


@api_router.get("/site-content")
async def public_site_content():
    return await _site_content()


@api_router.get("/admin/site-content")
async def admin_site_content(x_admin_token: Optional[str] = Header(None)):
    role = _require_admin(x_admin_token, "viewer")
    return {**(await _site_content()), "role": role}


@api_router.put("/admin/site-content")
async def update_admin_site_content(payload: SiteContentIn, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "editor")
    card_ids = [item.card_id for item in payload.featured_cards]
    if card_ids:
        existing = await db.cards.count_documents({"id": {"$in": card_ids}})
        if existing != len(set(card_ids)):
            raise HTTPException(status_code=422, detail="One or more featured cards do not exist")
    content = payload.model_dump()
    content["schema_version"] = SITE_CONTENT_VERSION
    content["updated_at"] = datetime.now(timezone.utc)
    await db.site_content.replace_one({"_id": "customer_site"}, {"_id": "customer_site", **content}, upsert=True)
    return _clean({**content})


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


@api_router.post("/admin/card-images")
async def upload_admin_card_image(request: Request, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "editor")
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Choose an image up to 2 MB.")
    try:
        image = await asyncio.to_thread(normalize_card_image, bytes(data))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    image_id = hashlib.sha256(image).hexdigest()
    await db.card_images.update_one({"_id": image_id}, {"$setOnInsert": {
        "data": image, "created_at": datetime.now(timezone.utc),
    }}, upsert=True)
    return {"path": f"/api/card-images/{image_id}", "content_type": "image/webp"}


@api_router.get("/card-images/{image_id}")
async def get_card_image(image_id: str):
    if not re.fullmatch(r"[a-f0-9]{64}", image_id):
        raise HTTPException(status_code=404, detail="Card image not found")
    image = await db.card_images.find_one({"_id": image_id})
    if not image:
        raise HTTPException(status_code=404, detail="Card image not found")
    return Response(content=image["data"], media_type="image/webp", headers={
        "Cache-Control": "public, max-age=31536000, immutable",
        "X-Content-Type-Options": "nosniff",
    })


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
    update = _apply_link_update(payload)
    result = await db.cards.update_one({"id": card_id, **CATALOG_QUERY}, update)
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Card not found")
    card = await db.cards.find_one({"id": card_id}, {"_id": 0})
    return {
        "id": card["id"],
        "official_apply_url": card.get("applyUrl"),
        "custom_apply_url": card.get("applyUrlOverride"),
        "effective_apply_url": card.get("applyUrlOverride") if card.get("applyUrlOverride") and card.get("applyLinkStatus") == "live" else card.get("applyUrl"),
        "partner_name": card.get("applyPartner"),
        "campaign_id": card.get("applyCampaignId"),
        "tracking_id": card.get("applyTrackingId"),
        "apply_link_status": card.get("applyLinkStatus", "official"),
        "expected_payout": card.get("expectedPayout"),
    }


async def _check_destination(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not _host_ok(parsed.hostname or "") or parsed.hostname in {"localhost", "localhost.localdomain"}:
        return {"healthy": False, "status_code": None, "final_url": None, "error": "Unsafe destination URL"}
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as checker:
            response = await checker.head(url)
            if response.status_code in {403, 405}:
                response = await checker.get(url, headers={"Range": "bytes=0-0"})
        final_url = str(response.url)
        healthy = response.status_code < 400 and urlparse(final_url).scheme == "https"
        return {"healthy": healthy, "status_code": response.status_code, "final_url": final_url, "error": None}
    except Exception as error:
        return {"healthy": False, "status_code": None, "final_url": None, "error": str(error)[:300]}


@api_router.post("/admin/check-apply-links")
async def check_apply_links(x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "publisher")
    return await _run_apply_link_checks()


async def _run_apply_link_checks():
    cards = await db.cards.find(CATALOG_QUERY, {"_id": 0}).to_list(None)
    semaphore = asyncio.Semaphore(10)
    async def inspect(card):
        partner_live = bool(card.get("applyUrlOverride") and card.get("applyLinkStatus") == "live")
        url = card.get("applyUrlOverride") if partner_live else card.get("applyUrl")
        if not url:
            return None
        async with semaphore:
            result = await _check_destination(url)
            record = {"card_id": card["id"], "card_name": card["name"], "issuer": card["issuer"],
                      "url": url, "link_type": "partner" if partner_live else "official", **result,
                      "checked_at": datetime.now(timezone.utc)}
            previous = await db.apply_link_checks.find_one({"card_id": card["id"], "link_type": record["link_type"]}, {"_id": 0}, sort=[("checked_at", -1)])
            await db.apply_link_checks.insert_one(dict(record))
            if not result["healthy"] and partner_live and previous and not previous.get("healthy"):
                await db.cards.update_one({"id": card["id"]}, {"$set": {"applyLinkStatus": "paused", "applyLinkPausedReason": "Automated destination check failed", "applyLinkUpdatedAt": datetime.now(timezone.utc)}})
                record["auto_paused"] = True
            return record
    checked = [item for item in await asyncio.gather(*(inspect(card) for card in cards)) if item]
    failed = sum(not item["healthy"] for item in checked)
    paused = sum(bool(item.get("auto_paused")) for item in checked)
    return {"checked": len(checked), "failed": failed, "auto_paused": paused, "results": [_clean(item) for item in checked]}


@api_router.get("/admin/apply-link-health")
async def apply_link_health(x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    records = await db.apply_link_checks.find({}, {"_id": 0}).sort("checked_at", -1).to_list(2000)
    latest = {}
    for item in records:
        latest.setdefault(item["card_id"], item)
    return {"links": list(latest.values()), "failed": sum(not item.get("healthy") for item in latest.values())}


@api_router.post("/admin/reconciliation-import")
async def reconciliation_import(rows: List[ReconciliationRowIn], x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token, "publisher")
    imported, matched = 0, 0
    for payload in rows:
        row = payload.model_dump()
        query = {key: row[key] for key in ("tracking_id", "campaign_id", "card_id") if row.get(key)}
        click = await db.apply_events.find_one(query, {"_id": 0}, sort=[("created_at", -1)]) if query else None
        if click:
            matched += 1
        document = {**row, "click_event_id": click.get("event_id") if click else None,
                    "partner_name": click.get("partner_name") if click else None,
                    "card_id": row.get("card_id") or (click or {}).get("card_id"),
                    "created_at": row.get("occurred_at") or datetime.now(timezone.utc),
                    "imported_at": datetime.now(timezone.utc)}
        result = await db.partner_conversions.update_one({"external_id": row["external_id"]}, {"$set": document}, upsert=True)
        imported += int(result.upserted_id is not None or result.modified_count > 0)
    return {"received": len(rows), "imported": imported, "matched": matched, "unmatched": len(rows) - matched}



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

    apply_events = await db.apply_events.find(q, {"_id": 0}).to_list(10000)
    partner_clicks = [event for event in apply_events if event.get("link_type") == "partner"]
    partner_counts: Dict[str, int] = {}
    for event in partner_clicks:
        name = event.get("partner_name") or "Unlabelled partner"
        partner_counts[name] = partner_counts.get(name, 0) + 1

    funnel_events = ["landing_view", "quiz_started", "result_viewed", "lead_submitted", "apply_clicked"]
    funnel = {}
    for event in funnel_events:
        funnel[event] = len(await db.product_events.distinct("session_id", {**q, "event": event}))

    conversions = await db.partner_conversions.find(q, {"_id": 0}).to_list(10000)
    conversion_counts = {status: sum(item.get("status") == status for item in conversions) for status in ("applied", "approved", "rejected", "reversed", "paid")}
    confirmed_revenue = round(sum(float(item.get("commission") or 0) for item in conversions if item.get("status") == "paid"), 2)
    experiments = []
    experiment_ids = await db.product_events.distinct("experiment_id", {**q, "experiment_id": {"$ne": None}})
    for experiment_id in experiment_ids:
        variants = await db.product_events.distinct("variant", {**q, "experiment_id": experiment_id})
        for variant in variants:
            visitors = len(await db.product_events.distinct("session_id", {**q, "experiment_id": experiment_id, "variant": variant, "event": "landing_view"}))
            handoffs = len(await db.product_events.distinct("session_id", {**q, "experiment_id": experiment_id, "variant": variant, "event": "apply_clicked"}))
            experiments.append({"experiment_id": experiment_id, "variant": variant, "visitors": visitors, "handoffs": handoffs,
                                "handoff_rate": round(handoffs * 100 / visitors, 1) if visitors else 0})

    return {
        "total_results": total,
        "emails_sent": emailed,
        "by_card": to_sorted(card_counts),
        "by_goal": to_sorted(goal_counts),
        "incomplete_sessions": incomplete,
        "funnel": funnel,
        "application_performance": {
            "total_clicks": len(apply_events),
            "partner_clicks": len(partner_clicks),
            "official_clicks": len(apply_events) - len(partner_clicks),
            "monetised_click_rate": round(len(partner_clicks) * 100 / len(apply_events)) if apply_events else 0,
            "expected_payout_pipeline": round(sum(float(event.get("expected_payout") or 0) for event in partner_clicks), 2),
            "by_partner": [
                {"label": name, "count": count, "pct": round(count * 100 / len(partner_clicks)) if partner_clicks else 0}
                for name, count in sorted(partner_counts.items(), key=lambda item: item[1], reverse=True)
            ],
            "confirmed_conversions": conversion_counts,
            "confirmed_revenue": confirmed_revenue,
            "reconciliation_match_rate": round(sum(bool(item.get("click_event_id")) for item in conversions) * 100 / len(conversions)) if conversions else 0,
        },
        "experiments": experiments,
    }


class PartialIn(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    answers: Dict[str, str] = {}
    step: int = Field(default=0, ge=0, le=100)
    reminder_consent: bool = False


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
                "reminder_consent": payload.reminder_consent,
                "reminder_consent_at": now if payload.reminder_consent else None,
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
        {"completed": {"$ne": True}, "reminder_sent": {"$ne": True}, "reminder_consent": True}, {"_id": 0}
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
@api_router.post("/ops/review-reminders")
async def send_review_reminders(x_admin_token: Optional[str] = Header(None), dry_run: bool = False):
    runner_token = os.environ.get("REMINDER_RUNNER_TOKEN", "")
    if not (runner_token and x_admin_token and secrets.compare_digest(runner_token, x_admin_token)):
        _require_admin(x_admin_token, "editor")
    now = datetime.now(timezone.utc)
    query = {"due_at": {"$lte": now}, "reminder_sent": False, "review_submitted": False, "review_consent": True, "delivery_state": {"$nin": ["claimed", "needs_review"]}}
    if dry_run:
        needs_review = await db.review_followups.count_documents({"$or": [
            {"delivery_state": "needs_review"},
            {"delivery_state": "claimed", "delivery_claimed_at": {"$lte": now - timedelta(minutes=15)}}]})
        return {"due": await db.review_followups.count_documents(query), "sent": 0, "dry_run": True, "needs_review": needs_review}
    due = await db.review_followups.find(query, {"_id": 0}).to_list(20)
    cards = await db.cards.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(None)
    names = {card["id"]: card["name"] for card in cards}
    sent = 0
    for followup in due:
        token = secrets.token_urlsafe(32)
        # Atomically claim before contacting the provider. A lost response must
        # not cause concurrent or later runners to send the same message twice.
        claimed = await db.review_followups.find_one_and_update(
            {**query, "followup_id": followup["followup_id"]},
            {"$set": {"delivery_state": "claimed", "delivery_claimed_at": now,
                      "token_hash": hashlib.sha256(token.encode()).hexdigest(),
                      "token_expires_at": now + timedelta(days=30)}})
        if not claimed:
            continue
        url = f"{PUBLIC_APP_URL}/#/review/{token}"
        card_name = names.get(followup["card_id"], "your card")
        html = (f'<table role="presentation" width="100%" style="font-family:Arial,sans-serif;background:#f6f7f5;padding:24px"><tr><td>'
                f'<h1 style="color:#0f1a17;font-size:22px">How is {escape(card_name)} working for you?</h1>'
                f'<p style="color:#55615c">Your experience can help other customers make a better decision. This link can be used once.</p>'
                f'<a href="{url}" style="display:inline-block;background:#0d9488;color:#fff;padding:12px 18px;border-radius:10px;text-decoration:none">Review this card</a>'
                f'<p style="color:#888;font-size:12px">This is the one review reminder you requested. It is not a marketing subscription.</p></td></tr></table>')
        try:
            await send_email(to=followup["email"], subject=f"Review your {card_name}", html=html)
            await db.review_followups.update_one({"followup_id": followup["followup_id"]}, {"$set": {"reminder_sent": True, "reminder_sent_at": now, "delivery_state": "sent"}})
            sent += 1
        except Exception as exc:
            await db.review_followups.update_one({"followup_id": followup["followup_id"]}, {"$set": {"delivery_state": "needs_review"}})
            logger.error("Review reminder delivery needs manual review")
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

async def _link_monitor_loop():
    await asyncio.sleep(300)
    interval = max(1, int(os.environ.get("APPLY_LINK_MONITOR_HOURS", "24"))) * 3600
    while True:
        try:
            summary = await _run_apply_link_checks()
            logger.info("Application-link monitor checked %s destinations; %s failed; %s auto-paused", summary["checked"], summary["failed"], summary["auto_paused"])
        except Exception as error:
            logger.error("Application-link monitor failed: %s", error)
        await asyncio.sleep(interval)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
