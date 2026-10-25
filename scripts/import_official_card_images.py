#!/usr/bin/env python3
"""Import card artwork from the official issuer pages listed in the catalog.

The importer is deliberately conservative: it only accepts raster images from
the same issuer host (or its CDN), requires a product-name match in the image
metadata/URL, validates the downloaded file, and records its source URL.
Review the result visually before publishing; an issuer's Open Graph image may
still be a promotional banner rather than the card face. Reviewed exact assets
are maintained in docs/catalog-artwork-sources.json.
"""

import argparse
import hashlib
import io
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "backend" / "cards_catalog.json"
OUTPUT = ROOT / "frontend" / "public" / "cards"
STOP = {"bank", "credit", "card", "cards", "the", "and", "plus", "india", "limited"}
CURATED_IMAGES = {
    "kotak-indigo-credit-card": "https://www.kotak.bank.in/content/dam/Kotak/product_card_images/indigo-credit-card-base-t.jpg",
    "kotak-indigo-premium-credit-card": "https://www.kotak.bank.in/content/dam/Kotak/product_card_images/indigo-xl-t.jpg",
    "kotak-white-reserve-credit-card": "https://www.kotak.bank.in/content/dam/Kotak/herosliderbanner/White-Reserve-Card_360x216.jpg",
    "kotak-white-credit-card": "https://www.kotak.bank.in/content/dam/Kotak/product_card_images/Thumbnail-Banners-for-white-t.jpg",
    "kotak-zen-credit-card": "https://www.kotak.bank.in/content/dam/Kotak/product_card_images/Thumbnail-Banners-for-Zen-t.jpg",
    "kotak-811-dream-different-credit-card": "https://www.kotak.bank.in/content/dam/Kotak/product_card_images/811-dream-different-credit-card-t.jpg",
}
REVIEWED_IMAGES = ROOT / "docs" / "catalog-artwork-sources.json"
if REVIEWED_IMAGES.exists():
    CURATED_IMAGES.update({item["id"]: item["source"] for item in json.loads(REVIEWED_IMAGES.read_text())})


def official_image_host(page, asset, curated=None):
    """Allow the issuer's own hosts, or an explicitly reviewed CDN asset."""
    if urlparse(asset).scheme != "https":
        return False
    if curated and asset == curated:
        return True
    issuer = (urlparse(page).hostname or "").removeprefix("www.")
    host = urlparse(asset).hostname or ""
    return bool(issuer) and (host == issuer or host.endswith("." + issuer))


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag in {"img", "source"}:
            for key in ("src", "data-src", "data-lazy-src"):
                if data.get(key):
                    self.items.append((data[key], data.get("alt", "")))
            for key in ("srcset", "data-srcset"):
                if data.get(key):
                    self.items.extend((part.strip().split()[0], data.get("alt", "")) for part in data[key].split(",") if part.strip())
        if tag == "meta" and data.get("property") in {"og:image", "twitter:image"} and data.get("content"):
            self.items.append((data["content"], data.get("property", "")))


def words(value):
    return {w for w in re.findall(r"[a-z0-9]+", value.lower()) if len(w) > 2 and w not in STOP}


def score(card, url, alt):
    alt = alt or ""
    haystack = words(url + " " + alt)
    wanted = words(card["name"])
    overlap = len(wanted & haystack)
    bonus = 2 if any(x in (url + alt).lower() for x in ("card", "credit-card", "credit_card")) else 0
    penalty = 4 if any(x in (url + alt).lower() for x in ("logo", "icon", "banner-mobile", "map-", "call-")) else 0
    return overlap * 5 + bonus - penalty, overlap


def image_info(data, content_type=""):
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            ext = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}.get(image.format)
            return (ext, *image.size) if ext else None
    except (UnidentifiedImageError, OSError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--ids", nargs="*", help="Only process these catalogue card IDs")
    parser.add_argument("--debug", action="store_true", help="Print candidate image diagnostics")
    args = parser.parse_args()
    cards = json.loads(CATALOG.read_text())
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 cardIQ catalog image verifier"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report_path = ROOT / "docs" / "card-image-import-report.json"
    prior_report = []
    if args.ids and report_path.exists():
        try:
            prior_report = json.loads(report_path.read_text())
        except Exception:
            prior_report = []
    report = []
    attempted = 0
    for card in cards:
        if args.ids and card["id"] not in args.ids:
            continue
        if card.get("imageUrl") and not args.overwrite:
            report.append({"id": card["id"], "status": "existing", "source": card.get("imageSourceUrl")})
            continue
        if args.limit and attempted >= args.limit:
            continue
        attempted += 1
        page = card["applyUrl"]
        try:
            response = session.get(page, timeout=20)
            response.raise_for_status()
            parser_ = Images(); parser_.feed(response.text)
            # Product pages choose their Open Graph image specifically for sharing.
            trusted_urls = {urljoin(page, raw) for raw, label in parser_.items if label in {"og:image", "twitter:image"}}
            curated = CURATED_IMAGES.get(card["id"])
            if curated:
                trusted_urls.add(curated)
                parser_.items.append((curated, card["name"]))
            # SBI exposes the authoritative face asset in its official product JSON.
            for source in card.get("sourceUrls", []):
                if source.endswith(".json"):
                    try:
                        product = session.get(source, timeout=20).json()
                        if product.get("cardImage"):
                            official_asset = urljoin(source, product["cardImage"])
                            trusted_urls.add(official_asset)
                            parser_.items.append((official_asset, card["name"]))
                    except Exception:
                        pass
            candidates = []
            for raw, alt in parser_.items:
                url = urljoin(page, raw)
                rank, overlap = score(card, url, alt)
                basename = Path(urlparse(url).path).name.lower()
                generic = any(term in basename for term in ("feecharges", "rightline", "category-bg", "mega-menu", "logo", "icon"))
                if official_image_host(page, url, curated) and not generic and (url in trusted_urls or overlap >= 2):
                    candidates.append((rank + (100 if url == curated else 0), url, alt))
            candidates.sort(reverse=True)
            if args.debug:
                print({"id": card["id"], "candidate_urls": [{"score": rank, "url": url, "alt": alt} for rank, url, alt in candidates[:12]]})
            accepted = None
            for rank, url, alt in candidates[:12]:
                try:
                    asset = session.get(url, timeout=20)
                    asset.raise_for_status()
                    info = image_info(asset.content, asset.headers.get("content-type", ""))
                    if not info:
                        if args.debug: print({"url": url, "rejected": "unsupported image"})
                        continue
                    ext, width, height = info
                    if width < 240 or height < 140:
                        if args.debug: print({"url": url, "rejected": "too small", "size": [width, height]})
                        continue
                    ratio = width / height
                    if not 0.5 <= ratio <= 2.8:
                        if args.debug: print({"url": url, "rejected": "aspect ratio", "size": [width, height]})
                        continue
                    digest = hashlib.sha256(asset.content).hexdigest()[:10]
                    filename = f"{card['id']}-{digest}.{ext}"
                    (OUTPUT / filename).write_bytes(asset.content)
                    card["imageUrl"] = f"/cards/{filename}"
                    card["imageSourceUrl"] = url
                    accepted = {"id": card["id"], "status": "imported", "source": url, "size": [width, height], "score": rank}
                    break
                except Exception:
                    continue
            report.append(accepted or {"id": card["id"], "status": "unresolved", "page": page, "candidates": len(candidates)})
        except Exception as exc:
            report.append({"id": card["id"], "status": "error", "page": page, "error": str(exc)})
        print(report[-1])
    CATALOG.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n")
    if args.ids:
        updated = {item["id"]: item for item in report}
        merged = [updated.pop(item["id"], item) for item in prior_report]
        merged.extend(updated.values())
        report = merged
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    imported = sum(bool(card.get("imageUrl")) for card in cards)
    print(f"Image coverage: {imported}/{len(cards)}")


if __name__ == "__main__":
    main()
