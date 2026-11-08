import asyncio
import importlib

import httpx
import pytest
from mongomock_motor import AsyncMongoMockClient

import issuer_source_monitor as monitor


def _html(*links):
    items = "".join(f'<a href="{href}">{title}</a>' for href, title in links)
    return f"<html><body>{items}</body></html>".encode()


def test_announcement_feed_baselines_then_queues_only_new_card_links(monkeypatch):
    async def run():
        db = AsyncMongoMockClient()["issuer_monitor_test"]
        listing = "https://issuer.example/news"
        article = "https://issuer.example/news/new-card"
        page = {"body": _html(("/news/old", "Old Bank Credit Card launch"),
                               ("/loans/new", "New home loan announcement"))}
        monkeypatch.setattr(monitor, "ANNOUNCEMENT_SOURCES", ({"issuer": "Example Bank", "url": listing},))
        monkeypatch.setattr(monitor, "_safe_url", lambda _url: asyncio.sleep(0, result=True))

        async def fetch(url, *args, **kwargs):
            assert url == listing
            return page["body"], "text/html", listing, {}

        monkeypatch.setattr(monitor, "_fetch_source", fetch)
        first = await monitor.run_issuer_source_check(db)
        assert first["new_announcements"] == 0
        assert await db.issuer_source_changes.count_documents({}) == 0

        page["body"] = _html(("/news/new-card", "Example Bank launches the Horizon Credit Card"),
                             ("/news/old", "Old Bank Credit Card launch"),
                             ("/loans/new", "New home loan announcement"))
        second = await monitor.run_issuer_source_check(db)
        assert second["new_announcements"] == 1
        record = await db.issuer_source_changes.find_one({"status": "pending"})
        assert record["issuer"] == "Example Bank"
        assert record["announcement_title"] == "Example Bank launches the Horizon Credit Card"
        assert record["announcement_url"] == article
        assert record["change_type"] == "new_card_announcement"

        repeated = await monitor.run_issuer_source_check(db)
        assert repeated["new_announcements"] == 0
        assert await db.issuer_source_changes.count_documents({}) == 1

    asyncio.run(run())


def test_fetch_source_follows_only_safe_redirects_and_sends_conditional_headers(monkeypatch):
    async def run():
        routes = []

        async def handle(request):
            routes.append(request)
            if request.url.host == "issuer.example":
                return httpx.Response(302, headers={"location": "https://trusted.example/terms"}, request=request)
            return httpx.Response(200, headers={"content-type": "text/plain", "etag": "next"}, content=b"terms", request=request)

        transport = httpx.MockTransport(handle)
        real_client = httpx.AsyncClient
        monkeypatch.setattr(monitor.httpx, "AsyncClient", lambda **kwargs: real_client(transport=transport, **kwargs))
        monkeypatch.setattr(monitor, "_safe_url", lambda url: asyncio.sleep(0, result="bad.example" not in url))
        body, content_type, final_url, headers = await monitor._fetch_source(
            "https://issuer.example/terms", etag="prior", last_modified="yesterday")
        assert body == b"terms"
        assert content_type == "text/plain"
        assert final_url == "https://trusted.example/terms"
        assert headers["etag"] == "next"
        assert routes[0].headers["if-none-match"] == "prior"
        assert routes[0].headers["if-modified-since"] == "yesterday"

        async def unsafe_handle(request):
            return httpx.Response(302, headers={"location": "https://bad.example/private"}, request=request)

        unsafe_transport = httpx.MockTransport(unsafe_handle)
        monkeypatch.setattr(monitor.httpx, "AsyncClient", lambda **kwargs: real_client(transport=unsafe_transport, **kwargs))
        with pytest.raises(ValueError, match="public HTTPS host"):
            await monitor._fetch_source("https://issuer.example/redirect")

    asyncio.run(run())


def test_fetch_source_rejects_oversized_responses(monkeypatch):
    async def run():
        response_body = b"x" * (monitor.MAX_SOURCE_BYTES + 1)

        async def handle(request):
            return httpx.Response(200, headers={"content-type": "text/plain"}, content=response_body, request=request)

        real_client = httpx.AsyncClient
        monkeypatch.setattr(monitor.httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(handle), **kwargs))
        monkeypatch.setattr(monitor, "_safe_url", lambda _url: asyncio.sleep(0, result=True))
        with pytest.raises(ValueError, match="5 MB"):
            await monitor._fetch_source("https://issuer.example/large")

    asyncio.run(run())


def test_changed_existing_terms_source_creates_review_item_with_diff(monkeypatch):
    async def run():
        db = AsyncMongoMockClient()["issuer_terms_test"]
        source = "https://issuer.example/card-terms"
        content = {"body": b"Annual fee: 500"}
        monkeypatch.setattr(monitor, "ANNOUNCEMENT_SOURCES", ())
        monkeypatch.setattr(monitor, "_safe_url", lambda _url: asyncio.sleep(0, result=True))

        async def fetch(url, *args, **kwargs):
            return content["body"], "text/plain", url, {"etag": "test"}

        monkeypatch.setattr(monitor, "_fetch_source", fetch)
        cards = [{"id": "example-card", "name": "Example Card", "issuer": "Example Bank", "sourceUrls": [source]}]
        first = await monitor.run_issuer_source_check(db, cards)
        assert first["baseline"] == 1

        content["body"] = b"Annual fee: 900"
        second = await monitor.run_issuer_source_check(db, cards)
        assert second["changed"] == 1
        change = await db.issuer_source_changes.find_one({"status": "pending"})
        assert change["cards"][0]["card_id"] == "example-card"
        assert "Annual fee: 900" in change["diff_preview"]

    asyncio.run(run())


def test_announcement_fetch_failure_is_reported_without_losing_other_results(monkeypatch):
    async def run():
        db = AsyncMongoMockClient()["issuer_monitor_failure_test"]
        monkeypatch.setattr(monitor, "ANNOUNCEMENT_SOURCES", ({"issuer": "Example Bank", "url": "https://issuer.example/news"},))

        async def fail(*args, **kwargs):
            raise TimeoutError("issuer timed out")

        monkeypatch.setattr(monitor, "_fetch_source", fail)
        summary = await monitor.run_issuer_source_check(db, cards=[])
        assert summary["announcement_sources_checked"] == 1
        assert summary["announcement_sources_failed"] == 1
        assert summary["new_announcements"] == 0
        state = await db.issuer_announcement_watch.find_one({"issuer": "Example Bank"})
        assert "timed out" in state["last_error"]

    asyncio.run(run())


def test_active_database_lease_prevents_duplicate_scan(monkeypatch):
    async def run():
        from datetime import datetime, timedelta, timezone

        db = AsyncMongoMockClient()["issuer_monitor_lease_test"]
        await db.issuer_source_monitor_locks.insert_one({
            "_id": "issuer-source-monitor",
            "owner": "another-process",
            "lease_until": datetime.now(timezone.utc) + timedelta(minutes=10),
        })
        result = await monitor.run_issuer_source_check(db, cards=[])
        assert result["skipped"] is True
        assert "already active" in result["skip_reason"]
        assert await db.issuer_announcement_watch.count_documents({}) == 0

    asyncio.run(run())


def test_expired_database_lease_is_reclaimed_and_released(monkeypatch):
    async def run():
        from datetime import datetime, timedelta, timezone

        db = AsyncMongoMockClient()["issuer_monitor_expired_lease_test"]
        await db.issuer_source_monitor_locks.insert_one({
            "_id": "issuer-source-monitor", "owner": "crashed-process",
            "lease_until": datetime.now(timezone.utc) - timedelta(minutes=1),
        })
        monkeypatch.setattr(monitor, "ANNOUNCEMENT_SOURCES", ())
        result = await monitor.run_issuer_source_check(db, cards=[])
        assert not result.get("skipped")
        assert result["sources_checked"] == 0
        assert await db.issuer_source_monitor_locks.count_documents({}) == 0

    asyncio.run(run())


def test_first_success_after_fetch_failure_establishes_baselines_without_false_alerts(monkeypatch):
    async def run():
        db = AsyncMongoMockClient()["issuer_monitor_recovery_test"]
        listing = "https://issuer.example/news"
        terms = "https://issuer.example/terms"
        listing_body = {"value": _html(("/news/existing", "Example Bank launches the Existing Credit Card"))}
        terms_body = {"value": b"Annual fee: 500"}
        attempts = {listing: 0, terms: 0}
        monkeypatch.setattr(monitor, "ANNOUNCEMENT_SOURCES", ({"issuer": "Example Bank", "url": listing},))
        monkeypatch.setattr(monitor, "_safe_url", lambda _url: asyncio.sleep(0, result=True))

        async def fetch(url, *args, **kwargs):
            attempts[url] += 1
            if attempts[url] == 1:
                raise TimeoutError("temporary timeout")
            if url == listing:
                return listing_body["value"], "text/html", url, {}
            return terms_body["value"], "text/plain", url, {}

        monkeypatch.setattr(monitor, "_fetch_source", fetch)
        cards = [{"id": "example-card", "name": "Example Card", "issuer": "Example Bank", "sourceUrls": [terms]}]
        failed = await monitor.run_issuer_source_check(db, cards)
        assert failed["failed"] == 1
        assert failed["announcement_sources_failed"] == 1

        recovered = await monitor.run_issuer_source_check(db, cards)
        assert recovered["baseline"] == 1
        assert recovered["new_announcements"] == 0
        assert await db.issuer_source_changes.count_documents({}) == 0

        listing_body["value"] = _html(("/news/new", "Example Bank announces its Horizon Credit Card"),
                                      ("/news/existing", "Example Bank launches the Existing Credit Card"))
        terms_body["value"] = b"Annual fee: 900"
        updated = await monitor.run_issuer_source_check(db, cards)
        assert updated["changed"] == 1
        assert updated["new_announcements"] == 1
        assert await db.issuer_source_changes.count_documents({"status": "pending"}) == 2

    asyncio.run(run())


def test_card_product_page_without_launch_language_is_not_a_candidate(monkeypatch):
    async def run():
        db = AsyncMongoMockClient()["issuer_monitor_noise_test"]
        listing = "https://issuer.example/news"
        monkeypatch.setattr(monitor, "ANNOUNCEMENT_SOURCES", ({"issuer": "Example Bank", "url": listing},))
        monkeypatch.setattr(monitor, "_safe_url", lambda _url: asyncio.sleep(0, result=True))

        async def fetch(url, *args, **kwargs):
            return _html(("/cards/product", "Example Bank Credit Card"),), "text/html", url, {}

        monkeypatch.setattr(monitor, "_fetch_source", fetch)
        summary = await monitor.run_issuer_source_check(db)
        assert summary["new_announcements"] == 0
        state = await db.issuer_announcement_watch.find_one({"issuer": "Example Bank"})
        assert state["candidate_count"] == 0

    asyncio.run(run())


def test_admin_review_queue_and_scan_enforce_roles_and_report_announcement_metrics(monkeypatch):
    async def run():
        server = importlib.import_module("server")
        db = AsyncMongoMockClient()["issuer_monitor_admin_test"]
        monkeypatch.setattr(server, "db", db)
        monkeypatch.setattr(server, "ADMIN_VIEWER_TOKEN", "source-viewer")
        monkeypatch.setattr(server, "ADMIN_EDITOR_TOKEN", "source-editor")
        monkeypatch.setattr(server, "ADMIN_PUBLISHER_TOKEN", "source-publisher")
        monkeypatch.setattr(server, "ADMIN_TOKEN", None)

        change_id = "a" * 64
        await db.issuer_source_changes.insert_one({
            "_id": change_id, "change_id": change_id, "source_id": change_id,
            "change_type": "new_card_announcement", "status": "pending",
            "detected_at": "2026-11-08T00:00:00Z", "issuer": "Example Bank",
        })
        await db.issuer_source_watch.insert_one({"_id": "terms-state", "source_id": "terms-state", "last_error": "unavailable"})
        await db.issuer_announcement_watch.insert_one({"_id": "news-state", "source_id": "news-state", "issuer": "Example Bank", "last_error": None})
        monkeypatch.setattr(server, "run_issuer_source_check", lambda _db: asyncio.sleep(0, result={
            "sources_checked": 2, "changed": 1, "baseline": 0, "unchanged": 1, "failed": 0,
            "announcement_sources_checked": 5, "new_announcements": 1,
            "announcement_sources_failed": 1, "announcement_results": [], "results": [],
        }))

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url="https://api.example") as client:
            assert (await client.get("/api/admin/issuer-source-changes")).status_code == 401
            viewer = {"X-Admin-Token": "source-viewer"}
            queue = (await client.get("/api/admin/issuer-source-changes", headers=viewer)).json()
            assert queue["pending"] == 1
            assert queue["sources_monitored"] == 2
            assert queue["sources_failing"] == 1
            assert (await client.post(f"/api/admin/issuer-source-changes/{change_id}/review",
                                      json={"status": "verified"}, headers=viewer)).status_code == 403
            editor = {"X-Admin-Token": "source-editor"}
            reviewed = await client.post(f"/api/admin/issuer-source-changes/{change_id}/review",
                                         json={"status": "verified", "review_note": "Confirmed official launch"}, headers=editor)
            assert reviewed.status_code == 200
            assert (await db.issuer_source_changes.find_one({"change_id": change_id}))["status"] == "verified"

            assert (await client.post("/api/admin/check-issuer-sources", headers=viewer)).status_code == 403
            publisher = {"X-Admin-Token": "source-publisher"}
            started = await client.post("/api/admin/check-issuer-sources", headers=publisher)
            assert started.status_code == 202
            scan_id = started.json()["scan_id"]
            for _ in range(30):
                scan = await client.get(f"/api/admin/issuer-source-scans/{scan_id}", headers=viewer)
                if scan.json()["status"] == "completed":
                    break
                await asyncio.sleep(0.01)
            assert scan.json()["status"] == "completed"
            assert scan.json()["announcement_sources_checked"] == 5
            assert scan.json()["new_announcements"] == 1

            monkeypatch.setattr(server, "run_issuer_source_check", lambda _db: asyncio.sleep(0, result={
                "sources_checked": 0, "changed": 0, "baseline": 0, "unchanged": 0, "failed": 0,
                "announcement_sources_checked": 0, "new_announcements": 0,
                "announcement_sources_failed": 0, "announcement_results": [], "results": [],
                "skipped": True, "skip_reason": "A source scan is already active on another API process.",
            }))
            second_started = await client.post("/api/admin/check-issuer-sources", headers=publisher)
            second_id = second_started.json()["scan_id"]
            for _ in range(30):
                skipped = await client.get(f"/api/admin/issuer-source-scans/{second_id}", headers=viewer)
                if skipped.json()["status"] == "skipped":
                    break
                await asyncio.sleep(0.01)
            assert skipped.json()["status"] == "skipped"
            assert "already active" in skipped.json()["error"]

    asyncio.run(run())
