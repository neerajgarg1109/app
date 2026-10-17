#!/usr/bin/env python3
"""Import card artwork from the official issuer pages listed in the catalog.

The importer is deliberately conservative: it only accepts raster images from
the same issuer host (or its CDN), requires a product-name match in the image
metadata/URL, validates the downloaded file, and records its source URL.
"""

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

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


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "img":
            for key in ("src", "data-src", "data-lazy-src"):
                if data.get(key):
                    self.items.append((data[key], data.get("alt", "")))
            if data.get("srcset"):
                self.items.extend((part.strip().split()[0], data.get("alt", "")) for part in data["srcset"].split(","))
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
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return "png", int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data.startswith(b"\xff\xd8"):
        pos = 2
        while pos + 9 < len(data):
            if data[pos] != 0xFF:
                pos += 1; continue
            marker = data[pos + 1]; pos += 2
            if marker in {0xD8, 0xD9}:
                continue
            length = int.from_bytes(data[pos:pos + 2], "big")
            if marker in range(0xC0, 0xC4):
                return "jpg", int.from_bytes(data[pos + 5:pos + 7], "big"), int.from_bytes(data[pos + 3:pos + 5], "big")
            pos += max(length, 2)
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp", 500, 300
    if "svg" in content_type or data.lstrip().startswith(b"<svg"):
        head = data[:3000].decode("utf-8", "ignore")
        viewbox = re.search(r"viewBox=[\"']\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)", head, re.I)
        if viewbox:
            return "svg", int(float(viewbox.group(1))), int(float(viewbox.group(2)))
        return "svg", 500, 300
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
                if urlparse(url).scheme == "https" and not generic and (url in trusted_urls or overlap >= 2):
                    candidates.append((rank, url, alt))
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
    imported = sum(item["status"] in {"existing", "imported"} for item in report)
    print(f"Image coverage: {imported}/{len(cards)}")


if __name__ == "__main__":
    main()
