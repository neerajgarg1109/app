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
from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime, timezone

from cards_seed import seed_cards, recommend_cards

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

logger = logging.getLogger(__name__)

# ---------------- Email (Emergent managed Resend) ----------------
EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ.get("EMERGENT_EMAIL_KEY")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "cardIQ")
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

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


class QuizSubmitIn(BaseModel):
    answers: Dict[str, str]
    lead: LeadIn


class CompareIn(BaseModel):
    ids: List[str]


def _clean(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


# ---------------- Routes ----------------
@api_router.get("/")
async def root():
    return {"message": "cardIQ API"}


@api_router.get("/cards")
async def get_cards():
    cards = await db.cards.find({}, {"_id": 0}).to_list(100)
    return cards


@api_router.get("/cards/{card_id}")
async def get_card(card_id: str):
    card = await db.cards.find_one({"id": card_id}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@api_router.post("/cards/compare")
async def compare_cards(payload: CompareIn):
    if not payload.ids:
        raise HTTPException(status_code=400, detail="No card ids provided")
    cards = await db.cards.find({"id": {"$in": payload.ids}}, {"_id": 0}).to_list(20)
    order = {cid: i for i, cid in enumerate(payload.ids)}
    cards.sort(key=lambda c: order.get(c["id"], 999))
    return cards


@api_router.post("/quiz/submit")
async def submit_quiz(payload: QuizSubmitIn):
    cards = await db.cards.find({}, {"_id": 0}).to_list(100)
    if not cards:
        raise HTTPException(status_code=503, detail="Card catalog unavailable")

    scored = recommend_cards(payload.answers, cards)
    top = scored[0]
    result_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    lead_id = str(uuid.uuid4())
    lead_doc = {
        "lead_id": lead_id,
        "name": payload.lead.name,
        "email": payload.lead.email,
        "phone": payload.lead.phone,
        "result_id": result_id,
        "created_at": now,
    }
    await db.leads.insert_one(dict(lead_doc))

    result_doc = {
        "result_id": result_id,
        "answers": payload.answers,
        "recommended_card_id": top["card"]["id"],
        "scored_ids": [s["card"]["id"] for s in scored],
        "lead_id": lead_id,
        "email_sent": False,
        "created_at": now,
    }
    await db.quiz_results.insert_one(dict(result_doc))

    # Mark any matching partial session as completed (so no reminder is sent)
    await db.partial_sessions.update_one(
        {"email": payload.lead.email}, {"$set": {"completed": True}}
    )

    # Best-effort welcome email the moment a lead submits (does not block the response on failure)
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
            {"card": s["card"], "score": s["score"], "confidence": s.get("confidence"), "reasons": s["reasons"]}
            for s in scored
        ],
    }


@api_router.get("/results/{result_id}")
async def get_result(result_id: str):
    result = await db.quiz_results.find_one({"result_id": result_id}, {"_id": 0})
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    cards = await db.cards.find({}, {"_id": 0}).to_list(100)
    scored = recommend_cards(result["answers"], cards)
    return {
        "result_id": result_id,
        "scored": [
            {"card": s["card"], "score": s["score"], "confidence": s.get("confidence"), "reasons": s["reasons"]}
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

    cards = await db.cards.find({}, {"_id": 0}).to_list(100)
    scored = recommend_cards(result["answers"], cards)
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



@api_router.get("/admin/leads")
async def admin_leads(date_from: Optional[str] = None, date_to: Optional[str] = None, x_admin_token: Optional[str] = Header(None)):
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    q = _date_query(date_from, date_to)
    leads = await db.leads.find(q, {"_id": 0}).sort("created_at", -1).to_list(2000)
    results = await db.quiz_results.find({}, {"_id": 0}).to_list(5000)
    res_map = {r["result_id"]: r for r in results}
    cards = await db.cards.find({}, {"_id": 0}).to_list(100)
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
    if not ADMIN_TOKEN or provided != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    q = _date_query(date_from, date_to)
    leads = await db.leads.find(q, {"_id": 0}).sort("created_at", -1).to_list(5000)
    results = await db.quiz_results.find({}, {"_id": 0}).to_list(10000)
    res_map = {r["result_id"]: r for r in results}
    cards = await db.cards.find({}, {"_id": 0}).to_list(100)
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
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    q = _date_query(date_from, date_to)
    results = await db.quiz_results.find(q, {"_id": 0}).to_list(10000)
    cards = await db.cards.find({}, {"_id": 0}).to_list(100)
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

    return {
        "total_results": total,
        "emails_sent": emailed,
        "by_card": to_sorted(card_counts),
        "by_goal": to_sorted(goal_counts),
        "incomplete_sessions": incomplete,
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
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
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



app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
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
    logger.info("cardIQ card catalog seeded")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
