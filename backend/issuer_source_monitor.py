"""Detect edits to issuer documents without changing published card facts."""

import asyncio
import difflib
import hashlib
import ipaddress
import re
import socket
import uuid
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument
from cards_seed import CARDS


MAX_SOURCE_BYTES = 5 * 1024 * 1024
MAX_TEXT_SNAPSHOT = 50_000
MAX_REDIRECTS = 4
USER_AGENT = "CardIQ-IssuerSourceMonitor/1.0 (+https://findmybest.cards)"
ALLOWED_SOURCE_HOSTS = frozenset(
    (urlparse(url).hostname or "").lower()
    for card in CARDS
    for url in card.get("sourceUrls", [])
    if isinstance(url, str) and url.startswith("https://")
)

# Curated official issuer listings, monitored for newly published card launches.
ANNOUNCEMENT_SOURCES = (
    {"issuer": "SBI Card", "url": "https://www.sbicard.com/en/who-we-are/media.page"},
    {"issuer": "Axis Bank", "url": "https://www.axis.bank.in/about-us/press-releases"},
    {"issuer": "IDFC FIRST Bank", "url": "https://www.idfcfirst.bank.in/about-us/news-and-media/press-releases"},
    {"issuer": "HDFC Bank", "url": "https://www.hdfc.bank.in/news-room"},
    {"issuer": "ICICI Bank", "url": "https://www.icici.bank.in/about-us/news/2004"},
)
ALLOWED_SOURCE_HOSTS = ALLOWED_SOURCE_HOSTS | frozenset(
    (urlparse(source["url"]).hostname or "").lower() for source in ANNOUNCEMENT_SOURCES
)
CARD_ANNOUNCEMENT_RE = re.compile(
    r"(?=.*\b(?:credit\s*cards?|cards?)\b)"
    r"(?=.*\b(?:new|launch(?:es|ed|ing)?|announc(?:e|es|ed|ement)|unveil(?:s|ed|ing)?|"
    r"introduc(?:e|es|ed|ing|tion)|debut(?:s|ed|ing)?|rolls?\s+out)\b)", re.I)


class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append({"href": href, "text_parts": []})
        if tag in {"script", "style", "noscript", "svg", "template", "head"}:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag == "a" and self.links:
            link = self.links[-1]
            link["text"] = " ".join(link.pop("text_parts"))
        if tag in {"script", "style", "noscript", "svg", "template", "head"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if self.links:
            text = re.sub(r"\s+", " ", data).strip()
            if text:
                self.links[-1]["text_parts"].append(text)
        if not self.skip_depth:
            text = re.sub(r"\s+", " ", data).strip()
            if text:
                self.parts.append(text)


def _safe_public_host(host):
    if not host or host.lower() in {"localhost", "localhost.localdomain"}:
        return False
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            resolved = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            addresses = [ipaddress.ip_address(item[4][0]) for item in resolved]
        except (OSError, ValueError):
            return False
    return bool(addresses) and all(address.is_global for address in addresses)


async def _safe_url(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or parsed.username or parsed.password or host not in ALLOWED_SOURCE_HOSTS:
        return False
    return await asyncio.to_thread(_safe_public_host, host)


async def _fetch_source(url, etag=None, last_modified=None):
    current = url
    headers = {"User-Agent": USER_AGENT}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    async with httpx.AsyncClient(timeout=httpx.Timeout(12), follow_redirects=False, trust_env=False) as client:
        for _ in range(MAX_REDIRECTS + 1):
            if not await _safe_url(current):
                raise ValueError("Source or redirect did not resolve to a public HTTPS host")
            async with client.stream("GET", current, headers=headers) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("Issuer source returned a redirect without a destination")
                    current = urljoin(str(response.url), location)
                    continue
                if response.status_code == 304:
                    return None, response.headers.get("content-type", "").split(";", 1)[0].lower(), str(response.url), response.headers
                response.raise_for_status()
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_SOURCE_BYTES:
                        raise ValueError("Issuer source exceeded the 5 MB monitoring limit")
                return bytes(body), response.headers.get("content-type", "").split(";", 1)[0].lower(), str(response.url), response.headers
    raise ValueError("Issuer source exceeded the redirect limit")


async def _content_fingerprint(body, content_type):
    if content_type in {"text/html", "application/xhtml+xml"}:
        parser = _VisibleText()
        parser.feed(body.decode("utf-8", errors="replace"))
        content = "\n".join(parser.parts)
        # Ignore whitespace-only edits and normalize Unicode before comparison.
        text_content = "\n".join(re.sub(r"\s+", " ", part).strip() for part in parser.parts if part.strip())
        normalized = re.sub(rb"\s+", b" ", content.encode("utf-8")).strip()
    elif content_type.startswith("text/") or content_type in {"application/json", "application/xml"}:
        text_content = body.decode("utf-8", errors="replace")
        normalized = re.sub(rb"\s+", b" ", body).strip()
    else:
        # PDFs and other binary issuer disclosures are monitored by bytes. A changed
        # file is a review candidate; this monitor does not infer changed terms.
        normalized = body
        text_content = None
    snapshot = text_content[:MAX_TEXT_SNAPSHOT] if text_content is not None else None
    return hashlib.sha256(normalized).hexdigest(), snapshot


async def _check_issuer_announcements(db, now):
    """Track newly appearing card-related links on curated official issuer pages."""
    results = []
    semaphore = asyncio.Semaphore(5)

    async def inspect(source):
        url, issuer = source["url"], source["issuer"]
        source_id = hashlib.sha256(("announcement:" + url).encode()).hexdigest()
        async with semaphore:
            try:
                body, content_type, final_url, _ = await _fetch_source(url)
                if body is None or content_type not in {"text/html", "application/xhtml+xml"}:
                    raise ValueError("Announcement listing did not return an HTML page")
                parser = _VisibleText()
                parser.feed(body.decode("utf-8", errors="replace"))
                candidates = {}
                for link in parser.links:
                    title = re.sub(r"\s+", " ", link.get("text", "")).strip()
                    if len(title) < 12 or not CARD_ANNOUNCEMENT_RE.search(title):
                        continue
                    article_url = urljoin(final_url, link["href"])
                    if not await _safe_url(article_url):
                        continue
                    candidates[article_url] = title[:300]

                state = await db.issuer_announcement_watch.find_one({"_id": source_id}, {"_id": 0})
                seen = set((state or {}).get("seen_urls", []))
                baseline_established = bool(state and "seen_urls" in state)
                discovered = 0
                if baseline_established:
                    for article_url, title in candidates.items():
                        if article_url in seen:
                            continue
                        announcement_id = hashlib.sha256((issuer + ":" + article_url).encode()).hexdigest()
                        record = {
                            "_id": announcement_id, "change_id": announcement_id,
                            # Give each announcement its own source_id so the existing
                            # pending-version uniqueness index cannot merge two launches.
                            "source_id": announcement_id, "source_url": url, "final_url": article_url,
                            "announcement_url": article_url, "announcement_title": title,
                            "issuer": issuer, "change_type": "new_card_announcement",
                            "content_type": "text/html", "cards": [], "status": "pending",
                            "diff_preview": None,
                            "diff_note": "New card-related link found on the issuer’s official announcement listing. Confirm that it describes a newly issued or announced card.",
                            "detected_at": now, "created_at": now,
                        }
                        await db.issuer_source_changes.update_one(
                            {"change_id": announcement_id}, {"$setOnInsert": record}, upsert=True)
                        discovered += 1
                # Baseline all current listing links on first scan; later scans queue unseen candidates.
                seen_urls = list((state or {}).get("seen_urls", []))
                if baseline_established:
                    seen_urls.extend(article_url for article_url in candidates if article_url not in seen)
                else:
                    seen_urls = list(candidates)
                await db.issuer_announcement_watch.update_one({"_id": source_id}, {"$set": {
                    "source_id": source_id, "source_url": url, "issuer": issuer,
                    "final_url": final_url, "seen_urls": seen_urls[-3000:],
                    "candidate_count": len(candidates), "baseline_established": True,
                    "checked_at": now, "last_error": None,
                }}, upsert=True)
                return {"source_url": url, "status": "checked", "candidates": len(candidates), "new_announcements": discovered}
            except Exception as error:
                await db.issuer_announcement_watch.update_one({"_id": source_id}, {"$set": {
                    "source_id": source_id, "source_url": url, "issuer": issuer,
                    "checked_at": now, "last_error": str(error)[:300],
                }}, upsert=True)
                return {"source_url": url, "status": "error", "error": str(error)[:200]}

    results = await asyncio.gather(*(inspect(source) for source in ANNOUNCEMENT_SOURCES))
    return {"announcement_sources_checked": len(results),
            "new_announcements": sum(item.get("new_announcements", 0) for item in results),
            "announcement_sources_failed": sum(item["status"] == "error" for item in results),
            "announcement_results": results}


async def _run_issuer_source_check(db, cards=None):
    """Check unique catalogue sources and create pending review records on change."""
    if cards is None:
        cards = await db.cards.find({"active": {"$ne": False}, "sourceUrls.0": {"$exists": True}},
                                    {"_id": 0, "id": 1, "name": 1, "issuer": 1, "sourceUrls": 1}).to_list(None)
    sources = {}
    for card in cards:
        for url in dict.fromkeys(card.get("sourceUrls") or []):
            if isinstance(url, str) and url.startswith("https://"):
                source = sources.setdefault(url, {"card_ids": [], "cards": []})
                source["card_ids"].append(card["id"])
                source["cards"].append({"card_id": card["id"], "card_name": card.get("name"), "issuer": card.get("issuer")})

    semaphore = asyncio.Semaphore(8)
    now = datetime.now(timezone.utc)

    async def inspect(url, references):
        source_id = hashlib.sha256(url.encode()).hexdigest()
        async with semaphore:
            try:
                state = await db.issuer_source_watch.find_one({"_id": source_id}, {"_id": 0})
                body, content_type, final_url, response_headers = await _fetch_source(
                    url, (state or {}).get("etag"), (state or {}).get("last_modified"))
                has_baseline = bool(state and state.get("digest"))
                if body is None:
                    if has_baseline:
                        await db.issuer_source_watch.update_one({"_id": source_id}, {"$set": {
                            "checked_at": now, "last_error": None,
                            "card_ids": references["card_ids"], "cards": references["cards"], "final_url": final_url,
                            "etag": response_headers.get("etag", state.get("etag")),
                            "last_modified": response_headers.get("last-modified", state.get("last_modified")),
                        }})
                        return {"source_url": url, "status": "unchanged"}
                    # A failed earlier attempt may have left stale validators behind;
                    # fetch the body unconditionally to establish the first baseline.
                    body, content_type, final_url, response_headers = await _fetch_source(url)
                    if body is None:
                        raise ValueError("Issuer source returned not-modified without a saved baseline")
                digest, snapshot = await _content_fingerprint(body, content_type)
                update = {"source_id": source_id, "source_url": url, "final_url": final_url,
                          "content_type": content_type, "digest": digest, "card_ids": references["card_ids"],
                          "cards": references["cards"], "checked_at": now, "last_error": None,
                          "etag": response_headers.get("etag"), "last_modified": response_headers.get("last-modified"),
                          "text_snapshot": snapshot}
                if has_baseline and state.get("digest") != digest:
                    pending_query = {"source_id": source_id, "current_digest": digest, "status": "pending"}
                    if not await db.issuer_source_changes.find_one(pending_query, {"_id": 1}):
                        change_id = hashlib.sha256(f"{source_id}:{state.get('digest')}:{digest}:{now.isoformat()}".encode()).hexdigest()
                        previous_text = state.get("text_snapshot")
                        diff_preview = None
                        if previous_text is not None and snapshot is not None:
                            diff_preview = "\n".join(difflib.unified_diff(
                                previous_text.splitlines(), snapshot.splitlines(),
                                fromfile="previous source text", tofile="current source text", lineterm=""))[:20_000]
                        try:
                            await db.issuer_source_changes.update_one(
                                pending_query,
                                {"$setOnInsert": {"_id": change_id, "change_id": change_id, "source_id": source_id, "source_url": url,
                            "final_url": final_url, "content_type": content_type, "previous_digest": state.get("digest"),
                            "current_digest": digest, "cards": references["cards"], "status": "pending",
                                    "diff_preview": diff_preview,
                                    "diff_note": None if diff_preview is not None else "Text diff is unavailable for this binary source or snapshot.",
                                    "detected_at": now, "created_at": now}}, upsert=True)
                        except DuplicateKeyError:
                            # Another running monitor already queued this source version.
                            pass
                await db.issuer_source_watch.update_one({"_id": source_id}, {"$set": update}, upsert=True)
                return {"source_url": url, "status": "changed" if has_baseline and state.get("digest") != digest else ("baseline" if not has_baseline else "unchanged")}
            except Exception as error:
                await db.issuer_source_watch.update_one(
                    {"_id": source_id},
                    {"$set": {"source_id": source_id, "source_url": url, "card_ids": references["card_ids"],
                               "cards": references["cards"], "checked_at": now, "last_error": str(error)[:300]}},
                    upsert=True)
                return {"source_url": url, "status": "error", "error": str(error)[:200]}

    results = await asyncio.gather(*(inspect(url, references) for url, references in sources.items()))
    announcements = await _check_issuer_announcements(db, now)
    return {"sources_checked": len(results), "changed": sum(item["status"] == "changed" for item in results),
            "baseline": sum(item["status"] == "baseline" for item in results),
            "unchanged": sum(item["status"] == "unchanged" for item in results),
            "failed": sum(item["status"] == "error" for item in results),
            **announcements, "checked_at": now, "results": results}


_source_scan_lock = asyncio.Lock()


async def run_issuer_source_check(db, cards=None):
    """Serialize scans within and across API processes with a recoverable DB lease."""
    async with _source_scan_lock:
        now = datetime.now(timezone.utc)
        owner = uuid.uuid4().hex
        lock_filter = {"_id": "issuer-source-monitor", "$or": [
            {"lease_until": {"$lte": now}}, {"lease_until": {"$exists": False}},
        ]}
        try:
            lease = await db.issuer_source_monitor_locks.find_one_and_update(
                lock_filter,
                {"$set": {"owner": owner, "lease_until": now + timedelta(hours=1), "acquired_at": now}},
                upsert=True, return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            # Another process owns the still-valid lease; its scan covers this interval.
            return {"sources_checked": 0, "changed": 0, "baseline": 0, "unchanged": 0,
                    "failed": 0, "announcement_sources_checked": 0, "new_announcements": 0,
                    "announcement_sources_failed": 0, "announcement_results": [], "results": [],
                    "checked_at": now, "skipped": True, "skip_reason": "A source scan is already active on another API process."}
        if not lease or lease.get("owner") != owner:
            return {"sources_checked": 0, "changed": 0, "baseline": 0, "unchanged": 0,
                    "failed": 0, "announcement_sources_checked": 0, "new_announcements": 0,
                    "announcement_sources_failed": 0, "announcement_results": [], "results": [],
                    "checked_at": now, "skipped": True, "skip_reason": "Could not acquire the source scan lease."}
        try:
            return await _run_issuer_source_check(db, cards)
        finally:
            await db.issuer_source_monitor_locks.delete_one({"_id": "issuer-source-monitor", "owner": owner})
