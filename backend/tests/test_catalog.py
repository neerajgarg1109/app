"""Catalog and migration regression tests; integration uses a disposable local DB."""
import asyncio
import importlib
import hashlib
import json
import os
import uuid
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from itertools import product
from urllib.parse import urlparse

import httpx
import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from cards_seed import CARDS, CATALOG_QUERY, DEMO_IDS, RECOMMENDABLE_QUERY, recommend_cards, seed_cards


def available_cards():
    return [c for c in CARDS if c.get("active") is not False
            and c.get("applicationsOpen") is not False
            and c.get("recommendationEligible") is not False]


def profile(**overrides):
    return dict(goal="travel", usage="flights", priority="lounge", fee="premium",
                spend="high", creditRoute="regular", **overrides)


def test_public_card_uses_only_live_partner_links_and_hides_campaign_metadata():
    server = importlib.import_module("server")
    official_url = "https://issuer.example/card"
    partner_url = "https://partner.example/apply"
    card = {
        "id": "partner-link-test",
        "applyUrl": official_url,
        "applyUrlOverride": partner_url,
        "applyPartner": "Example Partner",
        "applyCampaignId": "launch-2026",
        "applyTrackingId": "cardiq-card-page",
        "expectedPayout": 1250,
        "applyLinkUpdatedAt": datetime.now(timezone.utc),
    }

    live = server._card_for_client(dict(card, applyLinkStatus="live"))
    assert live["applyUrl"] == partner_url
    assert live["officialApplyUrl"] == official_url
    assert live["applicationLinkType"] == "partner"
    assert live["affiliateDisclosureRequired"] is True
    assert not ({"applyPartner", "applyCampaignId", "applyTrackingId", "expectedPayout", "applyLinkUpdatedAt"} & live.keys())

    for status in ("testing", "paused"):
        public = server._card_for_client(dict(card, applyLinkStatus=status))
        assert public["applyUrl"] == official_url
        assert public["applicationLinkType"] == "official"
        assert public["affiliateDisclosureRequired"] is False


def test_partner_link_configuration_validates_state_and_commercial_metadata():
    server = importlib.import_module("server")
    with pytest.raises(server.HTTPException, match="status must be testing, live or paused"):
        server._apply_link_update(server.ApplyLinkIn(apply_url="https://partner.example/apply", status="draft"))
    with pytest.raises(server.HTTPException, match="Partner name is required"):
        server._apply_link_update(server.ApplyLinkIn(apply_url="https://partner.example/apply", status="live"))
    with pytest.raises(server.HTTPException, match="Expected payout cannot be negative"):
        server._apply_link_update(server.ApplyLinkIn(
            apply_url="https://partner.example/apply", partner_name="Network", status="live", expected_payout=-1,
        ))

    testing = server._apply_link_update(server.ApplyLinkIn(
        apply_url=" https://partner.example/apply ", campaign_id=" launch ", tracking_id=" result ",
        status="testing", expected_payout=750,
    ))["$set"]
    assert testing["applyUrlOverride"] == "https://partner.example/apply"
    assert testing["applyPartner"] is None
    assert testing["applyCampaignId"] == "launch"
    assert testing["applyTrackingId"] == "result"
    assert testing["applyLinkStatus"] == "testing"
    assert testing["expectedPayout"] == 750
    assert testing["applyLinkUpdatedAt"].tzinfo is not None

    reset = server._apply_link_update(server.ApplyLinkIn(apply_url=None))
    assert set(reset["$unset"]) == {
        "applyUrlOverride", "applyPartner", "applyCampaignId", "applyTrackingId",
        "applyLinkStatus", "expectedPayout", "applyLinkUpdatedAt",
    }


def test_saved_results_refresh_changed_card_facts_and_value_estimates(monkeypatch):
    server = importlib.import_module("server")
    original = deepcopy(CARDS[0])
    changed = deepcopy(original)
    changed.update({
        "name": f"{original['name']} Updated", "annualFee": "₹9,999 + GST",
        "annualFeeAmount": 9999, "rewardLine": "Updated rewards proposition",
    })

    class Cursor:
        async def to_list(self, _limit):
            return [changed]

    class CardsCollection:
        def find(self, *_args, **_kwargs):
            return Cursor()

    class FakeDb:
        cards = CardsCollection()

    monkeypatch.setattr(server, "db", FakeDb())
    prior = recommend_cards(profile(), [original])[0]
    refreshed = asyncio.run(server.scored_result({"answers": profile(), "scored": [prior]}))[0]
    assert refreshed["card"]["name"].endswith(" Updated")
    assert refreshed["card"]["annualFeeAmount"] == 9999
    assert refreshed["card"]["rewardLine"] == "Updated rewards proposition"
    assert refreshed["valueEstimate"] != prior["valueEstimate"]


def test_saved_results_drop_newly_unavailable_cards_when_an_alternative_exists(monkeypatch):
    server = importlib.import_module("server")
    unavailable = deepcopy(CARDS[0])
    unavailable["applicationsOpen"] = False
    alternative = next(deepcopy(card) for card in CARDS[1:] if card.get("applicationsOpen") is not False and card.get("recommendationEligible") is not False)

    class Cursor:
        async def to_list(self, _limit):
            return [unavailable, alternative]

    class CardsCollection:
        def find(self, *_args, **_kwargs):
            return Cursor()

    class FakeDb:
        cards = CardsCollection()

    monkeypatch.setattr(server, "db", FakeDb())
    snapshots = recommend_cards(profile(), [CARDS[0], alternative], include_unavailable=True)
    refreshed = asyncio.run(server.scored_result({"answers": profile(), "scored": snapshots}))
    assert refreshed
    assert unavailable["id"] not in {item["card"]["id"] for item in refreshed}


def test_catalog_has_sourced_unique_real_cards():
    assert CARDS and len(CARDS) == len({c["id"] for c in CARDS})
    for card in CARDS:
        assert card["id"] not in DEMO_IDS
        assert card["feeType"] in {"free", "worth", "premium"}
        assert card["minSpend"] in {"low", "mid", "high", "vhigh"}
        assert card["creditReq"] in {"new", "fair", "good", "excellent"}
        assert len(card["palette"]) == 2 and card["accent"].startswith("#")
        assert card["annualFeeAmount"] >= 0 and card["joiningFeeAmount"] >= 0
        assert card["highlights"] and card["rewardLine"] and card["verifiedOn"]
        if card.get("recommendationEligible") is False:
            assert card["eligibilityNote"] and card["applicationsOpen"]
        assert card["ratingBasis"] and 0 <= card["rating"] <= 5
        assert card["applyUrl"] in card["sourceUrls"]
        for source in card["sourceUrls"]:
            parsed = urlparse(source)
            assert parsed.scheme == "https" and parsed.hostname
            assert parsed.hostname not in {"example.com", "www.example.com"}
            assert parsed.username is None


def test_scoring_excludes_paused_and_archived_cards():
    archived = dict(CARDS[0], id="archived-test", active=False)
    scored = recommend_cards(profile(), CARDS + [archived])
    assert len(scored) == len(available_cards())
    assert all(s["card"]["applicationsOpen"] and s["card"]["active"] for s in scored)
    assert all(35 <= s["confidence"] <= 99 for s in scored)
    assert [s["score"] for s in scored] == sorted([s["score"] for s in scored], reverse=True)


def test_every_valid_quiz_combination_returns_a_recommendation():
    choices = {
        "goal": ("travel", "shopping", "fuel", "cashback"),
        "spend": ("low", "mid", "high", "vhigh"),
        "fee": ("free", "worth", "premium"),
        "usage": ("online", "dining", "fuel", "flights"),
        "priority": ("lounge", "rewards", "forex", "cashback"),
        "creditRoute": ("regular", "secured", "either"),
    }
    keys = tuple(choices)
    for values in product(*(choices[key] for key in keys)):
        answers = dict(zip(keys, values))
        assert recommend_cards(answers, CARDS), answers


def test_international_travel_reason_does_not_invent_low_forex():
    atlas = next(c for c in CARDS if c["id"] == "axis-axis-bank-atlas-credit-card")
    # Historical/shared results can still contain the retired international answer.
    reasons = recommend_cards(profile(international="often"), [atlas])[0]["reasons"]
    assert "Travel rewards suit your overseas purchases" in reasons
    assert not any("forex" in reason.lower() for reason in reasons)


def test_secured_options_and_free_fee_profiles():
    answers = profile()
    answers.update(creditRoute="secured", fee="free", priority="forex", usage="online", spend="low")
    top = recommend_cards(answers, CARDS)[0]["card"]
    assert top["secured"] and top["creditReq"] == "new"
    assert top["feeType"] == "free"
    assert any("fixed deposit" in h.lower() for h in top["highlights"])


def test_migration_and_api_round_trip(monkeypatch):
    async def run():
        mongo_url = os.environ.get("CARDIQ_TEST_MONGO_URL", "mongodb://127.0.0.1:27017")
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        await client.admin.command("ping")
        name = "cardiq_catalog_test_" + uuid.uuid4().hex
        database = client[name]
        monkeypatch.setenv("MONGO_URL", mongo_url)
        monkeypatch.setenv("DB_NAME", name)
        server = importlib.import_module("server")
        monkeypatch.setattr(server, "db", database)
        monkeypatch.setattr(server, "EMAIL_KEY", None)
        monkeypatch.setattr(server, "ADMIN_TOKEN", uuid.uuid4().hex)
        monkeypatch.setattr(server, "ADMIN_VIEWER_TOKEN", "viewer-token")
        monkeypatch.setattr(server, "ADMIN_EDITOR_TOKEN", "editor-token")
        monkeypatch.setattr(server, "ADMIN_PUBLISHER_TOKEN", "publisher-token")
        sent_emails = []
        async def fake_send_email(**message):
            server._assert_safe_email(message["subject"], message["html"])
            sent_emails.append(message)
            return "test-email-id"
        monkeypatch.setattr(server, "send_email", fake_send_email)
        try:
            demo = dict(deepcopy(CARDS[0]), id=DEMO_IDS[0], name="Historical demo", active=True)
            await database.cards.insert_one(dict(demo))
            await seed_cards(database)
            await seed_cards(database)
            assert await database.cards.count_documents(CATALOG_QUERY) == len(CARDS)
            assert await database.cards.count_documents({}) == len(CARDS) + 1
            assert (await database.cards.find_one({"id": demo["id"]}))["active"] is False
            # Seed must preserve user-created records rather than deleting everything else.
            custom = dict(deepcopy(CARDS[0]), id="user-card")
            await database.cards.insert_one(custom)
            await seed_cards(database)
            assert (await database.cards.find_one({"id": "user-card"}))["active"] is True
            await database.cards.delete_one({"id": "user-card"})
            transport = httpx.ASGITransport(app=server.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as api:
                headers = {"X-Admin-Token": server.ADMIN_TOKEN}
                viewer_headers = {"X-Admin-Token": "viewer-token"}
                editor_headers = {"X-Admin-Token": "editor-token"}
                publisher_headers = {"X-Admin-Token": "publisher-token"}
                assert (await api.get("/api/")).json() == {"message": "cardIQ API"}
                assert (await api.get("/api/admin/cards")).status_code == 401
                assert (await api.get("/api/admin/cards", headers=viewer_headers)).status_code == 200
                admin_catalog = await api.get("/api/admin/cards", headers=headers)
                assert admin_catalog.status_code == 200 and len(admin_catalog.json()["cards"]) == len(CARDS)
                managed_payload = {
                    "name": "Admin Test Card", "issuer": "Test Bank", "variants": ["Visa", "RuPay"],
                    "network": "Visa", "rewardLine": "Test rewards", "applyUrl": "https://bank.example.org/card",
                    "rewardCurrency": "Test Points", "rewardRedemption": "One point is worth ₹0.50.",
                    "welcomeBenefits": ["1,000 points after eligible first spend"],
                    "milestoneBenefits": ["Voucher on ₹1 lakh annual spend"],
                    "loungeBenefits": ["Two domestic visits each quarter"],
                    "exclusions": ["No rewards on rent"], "forexMarkup": "2% + GST",
                    "fuelBenefits": "1% surcharge waiver", "eligibilityNote": "Issuer approval applies.",
                    "sourceUrls": ["https://bank.example.org/card/terms"],
                }
                created_card = await api.post("/api/admin/cards", json=managed_payload, headers=headers)
                assert created_card.status_code == 201 and created_card.json()["variants"] == ["Visa", "RuPay"]
                assert created_card.json()["welcomeBenefits"] == managed_payload["welcomeBenefits"]
                assert "https://bank.example.org/card/terms" in created_card.json()["sourceUrls"]
                assert (await api.post("/api/admin/cards", json=managed_payload, headers=viewer_headers)).status_code == 403
                managed_id = created_card.json()["id"]
                managed_payload.update({"name": "Edited Admin Test Card", "variants": ["Mastercard"]})
                edited_card = await api.put(f"/api/admin/cards/{managed_id}", json=managed_payload, headers=headers)
                assert edited_card.status_code == 200 and edited_card.json()["name"] == "Edited Admin Test Card"
                assert (await api.post(f"/api/admin/cards/{managed_id}/publish", headers=editor_headers)).status_code == 403
                await seed_cards(database)
                assert (await database.cards.find_one({"id": managed_id}))["draft"]["name"] == "Edited Admin Test Card"
                published_card = await api.post(f"/api/admin/cards/{managed_id}/publish", headers=headers)
                assert published_card.status_code == 200 and published_card.json()["publication_status"] == "published"
                assert (await database.cards.find_one({"id": managed_id}))["name"] == "Edited Admin Test Card"
                managed_payload.update({"name": "Version Two Admin Card"})
                assert (await api.put(f"/api/admin/cards/{managed_id}", json=managed_payload, headers=editor_headers)).status_code == 200
                assert (await api.post(f"/api/admin/cards/{managed_id}/publish", headers=publisher_headers)).status_code == 200
                history = await api.get(f"/api/admin/cards/{managed_id}/history", headers=viewer_headers)
                assert history.status_code == 200 and len(history.json()["versions"]) == 1
                version_id = history.json()["versions"][0]["version_id"]
                rollback = await api.post(f"/api/admin/cards/{managed_id}/rollback/{version_id}", headers=publisher_headers)
                assert rollback.status_code == 200 and rollback.json()["has_draft"] is True
                assert (await api.delete(f"/api/admin/cards/{managed_id}/draft", headers=editor_headers)).status_code == 200
                assert (await api.post(f"/api/admin/cards/{managed_id}/archive", headers=publisher_headers)).json()["publication_status"] == "archived"
                assert (await api.post(f"/api/admin/cards/{managed_id}/restore", headers=publisher_headers)).json()["publication_status"] == "published"
                await database.cards.delete_one({"id": managed_id})
                discard = await api.post("/api/admin/cards", json={**managed_payload, "name": "Discard Me"}, headers=editor_headers)
                discard_id = discard.json()["id"]
                deleted = await api.delete(f"/api/admin/cards/{discard_id}/draft", headers=editor_headers)
                assert deleted.json() == {"deleted": True, "id": discard_id}
                assert (await api.get("/api/admin/cards-export", params={"format": "xml"}, headers=headers)).status_code == 422
                export_json = await api.get("/api/admin/cards-export", headers=viewer_headers)
                assert export_json.status_code == 200 and len(export_json.json()["cards"]) == len(CARDS)
                export_csv = await api.get("/api/admin/cards-export", params={"format": "csv"}, headers=viewer_headers)
                assert export_csv.status_code == 200 and export_csv.text.startswith("id,name,issuer")
                dry_import = await api.post("/api/admin/cards-import", params={"dry_run": "true"}, json=[managed_payload], headers=editor_headers)
                assert dry_import.json()["valid"] is True and dry_import.json()["cards"] == 1
                real_import = await api.post("/api/admin/cards-import", params={"dry_run": "false"}, json=[{**managed_payload, "name": "Imported Card"}], headers=editor_headers)
                assert real_import.json()["created"] == 1
                await database.cards.delete_one({"id": real_import.json()["ids"][0]})
                override_card = CARDS[0]
                invalid = await api.put(
                    f"/api/admin/cards/{override_card['id']}/apply-link",
                    json={"apply_url": "http://unsafe.example.com"}, headers=headers,
                )
                assert invalid.status_code == 422
                custom_apply_url = "https://partner.example.org/apply/cardiq"
                updated = await api.put(
                    f"/api/admin/cards/{override_card['id']}/apply-link",
                    json={"apply_url": custom_apply_url, "partner_name": "Partner Network", "campaign_id": "launch-1", "tracking_id": "track-1", "status": "live", "expected_payout": 1250}, headers=headers,
                )
                assert updated.status_code == 200
                assert updated.json()["effective_apply_url"] == custom_apply_url
                assert updated.json()["partner_name"] == "Partner Network"
                response = await api.get("/api/cards")
                assert response.status_code == 200 and len(response.json()) == len(CARDS)
                public_override = next(c for c in response.json() if c["id"] == override_card["id"])
                assert public_override["applyUrl"] == custom_apply_url
                assert public_override["officialApplyUrl"] == override_card["applyUrl"]
                assert public_override["applicationLinkType"] == "partner"
                assert public_override["affiliateDisclosureRequired"] is True
                restricted_ids = {c["id"] for c in CARDS if c.get("recommendationEligible") is False}
                assert restricted_ids <= {c["id"] for c in response.json()}
                ids = [CARDS[-1]["id"], CARDS[0]["id"]]
                response = await api.post("/api/cards/compare", json={"ids": ids})
                assert [c["id"] for c in response.json()] == ids
                assert (await api.post("/api/cards/compare", json={"ids": []})).status_code == 400
                assert (await api.get(f"/api/cards/{CARDS[0]['id']}")).status_code == 200
                assert (await api.get("/api/cards/missing-card")).status_code == 404
                assert (await api.post(f"/api/cards/{CARDS[0]['id']}/apply-click", json={"result_id": None})).status_code == 200
                assert await database.apply_events.count_documents({"card_id": CARDS[0]["id"]}) == 1
                click = await database.apply_events.find_one({"card_id": CARDS[0]["id"]})
                assert click["partner_name"] == "Partner Network" and click["campaign_id"] == "launch-1"
                assert (await api.post("/api/cards/missing-card/apply-click", json={})).status_code == 404
                assert (await api.post(f"/api/cards/{CARDS[0]['id']}/report", json={"issue": "too short"})).status_code == 422
                report = await api.post(f"/api/cards/{CARDS[0]['id']}/report", json={"issue": "The annual fee appears to have changed.", "email": "reporter@example.com"})
                assert report.status_code == 200 and await database.card_reports.count_documents({"card_id": CARDS[0]["id"]}) == 1
                assert (await api.post("/api/cards/missing-card/report", json={"issue": "This is a sufficiently long report."})).status_code == 404
                anonymous = await api.post("/api/quiz/submit", json={"answers": profile()})
                assert anonymous.status_code == 200
                anonymous_id = anonymous.json()["result_id"]
                anonymous_doc = await database.quiz_results.find_one({"result_id": anonymous_id})
                assert anonymous_doc["lead_id"] is None
                assert (await api.post(f"/api/results/{anonymous_id}/lead", json={
                    "name": "asdf", "email": "valid@example.com", "phone": "9876543210"
                })).status_code == 422
                assert (await api.post(f"/api/results/{anonymous_id}/lead", json={
                    "name": "Valid Name", "email": "not-an-email", "phone": "9876543210"
                })).status_code == 422
                assert (await api.post(f"/api/results/{anonymous_id}/lead", json={
                    "name": "Valid Name", "email": "valid@example.com", "phone": "12345"
                })).status_code == 422
                attached = await api.post(f"/api/results/{anonymous_id}/lead", json={
                    "name": "Optional contact", "email": "optional@example.com",
                    "phone": "+91 98765 43210", "contact_consent": True,
                })
                assert attached.status_code == 200
                anonymous_doc = await database.quiz_results.find_one({"result_id": anonymous_id})
                assert anonymous_doc["lead_id"]
                attached_lead = await database.leads.find_one({"lead_id": anonymous_doc["lead_id"]})
                assert attached_lead["contact_consent"] is True and attached_lead["consent_recorded_at"]
                assert attached_lead["phone"] == "+919876543210"
                emailed = await api.post(f"/api/results/{anonymous_id}/email")
                assert emailed.status_code == 200 and emailed.json()["sent_to"] == "optional@example.com"
                assert (await database.quiz_results.find_one({"result_id": anonymous_id}))["email_sent"] is True
                assert (await api.post("/api/results/missing/email")).status_code == 404
                no_contact = await api.post("/api/quiz/submit", json={"answers": profile()})
                assert (await api.post(f"/api/results/{no_contact.json()['result_id']}/email")).status_code == 404
                response = await api.post("/api/quiz/submit", json={"answers": profile(),
                    "lead": {"name": "Catalog test", "email": "local-test@example.com"}})
                assert response.status_code == 200, response.text
                result = response.json()
                assert len(result["scored"]) == len(available_cards())
                assert not restricted_ids & {s["card"]["id"] for s in result["scored"]}
                feedback = await api.post("/api/experience-feedback", json={
                    "rating": 4, "feedback": "Clear recommendation and useful trade-offs.",
                    "result_id": result["result_id"], "card_id": result["scored"][0]["card"]["id"],
                })
                assert feedback.status_code == 201
                stored_feedback = await database.experience_feedback.find_one({"result_id": result["result_id"]})
                assert stored_feedback["rating"] == 4 and stored_feedback["feedback"].startswith("Clear recommendation")
                assert (await api.post("/api/experience-feedback", json={"rating": 6})).status_code == 422
                assert (await api.post("/api/experience-feedback", json={"rating": 5, "feedback": "x" * 1501})).status_code == 422
                assert (await api.post("/api/experience-feedback", json={"rating": 5, "card_id": "missing"})).status_code == 404
                top_id = result["scored"][0]["card"]["id"]
                denied_followup = await api.post(f"/api/cards/{top_id}/review-followup", json={
                    "email": "holder@example.com", "result_id": result["result_id"], "review_consent": False,
                })
                assert denied_followup.status_code == 422
                followup = await api.post(f"/api/cards/{top_id}/review-followup", json={
                    "email": "Holder@Example.com", "result_id": result["result_id"], "review_consent": True,
                })
                assert followup.status_code == 200 and followup.json()["due_in_days"] == 75
                followup_doc = await database.review_followups.find_one({"email": "holder@example.com", "card_id": top_id})
                assert followup_doc["marketing_consent"] is False and followup_doc["review_consent"] is True
                review_token = "single-use-review-token"
                await database.review_followups.update_one({"followup_id": followup_doc["followup_id"]}, {"$set": {
                    "token_hash": hashlib.sha256(review_token.encode()).hexdigest(),
                    "token_expires_at": datetime.now(timezone.utc) + timedelta(days=1),
                }})
                invite = await api.get(f"/api/reviews/invite/{review_token}")
                assert invite.status_code == 200 and invite.json()["card"]["id"] == top_id
                review_payload = {"overall": 5, "rewards": 4, "redemption": 4, "service": 3,
                                  "app_experience": 4, "acceptance": 5, "current_holder": True,
                                  "comments": "Useful card after several months."}
                assert (await api.post(f"/api/reviews/invite/{review_token}", json={**review_payload, "current_holder": False})).status_code == 422
                submitted_review = await api.post(f"/api/reviews/invite/{review_token}", json=review_payload)
                assert submitted_review.status_code == 200
                assert (await api.post(f"/api/reviews/invite/{review_token}", json=review_payload)).status_code == 404
                pending_review = await database.cardholder_reviews.find_one({"followup_id": followup_doc["followup_id"]})
                admin_reviews = await api.get("/api/admin/card-reviews", headers=viewer_headers)
                assert any(item["review_id"] == pending_review["review_id"] for item in admin_reviews.json()["reviews"])
                assert (await api.put(f"/api/admin/card-reviews/{pending_review['review_id']}", json={"status": "approved"}, headers=editor_headers)).status_code == 403
                assert (await api.put(f"/api/admin/card-reviews/{pending_review['review_id']}", json={"status": "invalid"}, headers=publisher_headers)).status_code == 422
                assert (await api.put(f"/api/admin/card-reviews/{pending_review['review_id']}", json={"status": "approved"}, headers=publisher_headers)).status_code == 200
                # Public community ratings stay hidden until the minimum sample is reached.
                base_review = {key: 4 for key in ("overall", "rewards", "redemption", "service", "app_experience", "acceptance")}
                existing_approved = await database.cardholder_reviews.count_documents({"card_id": top_id, "status": "approved"})
                for index in range(existing_approved, 19):
                    await database.cardholder_reviews.insert_one({**base_review, "review_id": f"rating-{index}", "card_id": top_id, "status": "approved"})
                hidden_rating = await api.get(f"/api/cards/{top_id}/community-rating")
                assert hidden_rating.json() == {"published": False, "count": 19, "minimum": 20}
                await database.cardholder_reviews.insert_one({**base_review, "overall": 5, "review_id": "rating-20", "card_id": top_id, "status": "approved"})
                public_rating = await api.get(f"/api/cards/{top_id}/community-rating")
                assert public_rating.json()["published"] is True and public_rating.json()["count"] == 20
                # Due reminders create one-time review links and are never marketing subscriptions.
                await database.review_followups.insert_one({
                    "followup_id": "due-followup", "email": "due@example.com", "card_id": top_id,
                    "due_at": datetime.now(timezone.utc) - timedelta(days=1), "reminder_sent": False,
                    "review_submitted": False, "review_consent": True,
                })
                reminders = await api.post("/api/admin/send-review-reminders", headers=editor_headers)
                assert reminders.json() == {"due": 1, "sent": 1}
                due_doc = await database.review_followups.find_one({"followup_id": "due-followup"})
                assert due_doc["reminder_sent"] is True and due_doc["token_hash"] and due_doc["token_expires_at"]
                # Current issuer facts must flow through previously shared results and later emails.
                top = result["scored"][0]["card"]
                await database.cards.update_one({"id": top["id"]}, {"$set": {"name": "Updated issuer name", "active": False}})
                saved = await api.get("/api/results/" + result["result_id"])
                saved_top = next(s["card"] for s in saved.json()["scored"] if s["card"]["id"] == top["id"])
                assert saved_top["name"] == "Updated issuer name"
                reset = await api.put(
                    f"/api/admin/cards/{override_card['id']}/apply-link",
                    json={"apply_url": None}, headers=headers,
                )
                assert reset.status_code == 200 and reset.json()["custom_apply_url"] is None
                refreshed = await api.get("/api/results/" + result["result_id"])
                refreshed_card = next(s["card"] for s in refreshed.json()["scored"] if s["card"]["id"] == override_card["id"])
                assert refreshed_card["applyUrl"] == override_card["applyUrl"]
                doc = await database.quiz_results.find_one({"result_id": result["result_id"]})
                assert next(s["card"] for s in await server.scored_result(doc) if s["card"]["id"] == top["id"])["name"] == "Updated issuer name"
                await database.quiz_results.insert_one({"result_id": "legacy", "answers": profile(), "scored_ids": [demo["id"]]})
                legacy = await api.get("/api/results/legacy")
                assert legacy.status_code == 200
                assert legacy.json()["scored"][0]["card"]["name"] == "Historical demo"
                assert (await api.get("/api/admin/leads")).status_code == 401
                preview = await api.post(f"/api/admin/cards/{CARDS[0]['id']}/recommendation-preview", json={"answers": profile()}, headers=viewer_headers)
                live_recommendable = await database.cards.count_documents(RECOMMENDABLE_QUERY)
                assert preview.status_code == 200 and preview.json()["total"] == live_recommendable
                assert (await api.post("/api/admin/cards/missing/recommendation-preview", json={"answers": profile()}, headers=viewer_headers)).status_code == 404
                status_created = await api.post("/api/status", json={"client_name": "integration-suite"})
                assert status_created.status_code == 200 and status_created.json()["client_name"] == "integration-suite"
                assert any(item["client_name"] == "integration-suite" for item in (await api.get("/api/status")).json())
                partial = await api.post("/api/quiz/partial", json={
                    "name": "Resume User", "email": "resume@example.com", "answers": {"goal": "travel"}, "step": 2,
                })
                assert partial.status_code == 200
                reminder_result = await api.post("/api/admin/send-reminders", headers=editor_headers)
                assert reminder_result.json()["reminders_sent"] == 1
                assert (await database.partial_sessions.find_one({"email": "resume@example.com"}))["reminder_sent"] is True
                # Catalog growth must not truncate legacy rankings or admin names
                # at the former 100-card cursor limit.
                await database.quiz_results.insert_one({"result_id": "expanded-legacy",
                    "answers": profile(), "scored_ids": [c["id"] for c in CARDS],
                    "recommended_card_id": CARDS[-1]["id"]})
                await database.leads.insert_one({"lead_id": "expanded-lead", "name": "Expanded catalog",
                    "email": "expanded@example.com", "result_id": "expanded-legacy"})
                expanded = await api.get("/api/results/expanded-legacy")
                assert len(expanded.json()["scored"]) == len(CARDS)
                leads = (await api.get("/api/admin/leads", headers=headers)).json()["leads"]
                assert next(l for l in leads if l["result_id"] == "expanded-legacy")["recommended_card"] == CARDS[-1]["name"]
                for event in ("landing_view", "quiz_started", "result_viewed", "lead_submitted", "apply_clicked"):
                    tracked = await api.post("/api/product-events", json={
                        "event": event, "session_id": "anonymous-session-1234", "result_id": result["result_id"],
                    })
                    assert tracked.status_code == 202
                shared = await api.post("/api/product-events", json={
                    "event": "content_shared", "session_id": "anonymous-session-1234",
                    "card_id": CARDS[0]["id"], "channel": "whatsapp", "page_type": "card",
                })
                assert shared.status_code == 202
                assert await database.product_events.count_documents({
                    "event": "content_shared", "card_id": CARDS[0]["id"], "channel": "whatsapp",
                }) == 1
                assert (await api.post("/api/product-events", json={
                    "event": "content_shared", "session_id": "anonymous-session-1234",
                    "channel": "email", "page_type": "card",
                })).status_code == 422
                assert (await api.post("/api/product-events", json={
                    "event": "content_shared", "session_id": "anonymous-session-1234",
                    "card_id": "not a safe id", "channel": "copy", "page_type": "card",
                })).status_code == 422
                # Events are idempotent for one session/result combination.
                await api.post("/api/product-events", json={
                    "event": "landing_view", "session_id": "anonymous-session-1234", "result_id": result["result_id"],
                })
                assert await database.product_events.count_documents({"session_id": "anonymous-session-1234"}) == 6
                assert (await api.post("/api/product-events", json={
                    "event": "unknown", "session_id": "anonymous-session-1234",
                })).status_code == 422
                csv = await api.get("/api/admin/leads.csv", headers=headers)
                assert csv.status_code == 200 and CARDS[-1]["name"] in csv.text
                insights = await api.get("/api/admin/insights", headers=headers)
                assert insights.status_code == 200 and CARDS[-1]["name"] in insights.text
                assert insights.json()["funnel"] == {event: 1 for event in (
                    "landing_view", "quiz_started", "result_viewed", "lead_submitted", "apply_clicked"
                )}
                assert insights.json()["application_performance"]["partner_clicks"] == 1
        finally:
            await client.drop_database(name)
            client.close()
    asyncio.run(run())


def test_hdfc_partner_sources_and_reward_currency():
    tata_neu = [c for c in CARDS if c["id"] in {"hdfc-tata-neu-infinity", "hdfc-tata-neu-plus"}]
    assert len(tata_neu) == 2
    assert {c["annualFeeAmount"] for c in tata_neu} == {499, 1499}
    for card in tata_neu:
        assert card["rewardCurrency"] == "NeuCoins"
        assert "cashback" not in card["bestFor"]
        assert card["verificationSourceType"] == "official_co_brand_partner"
        assert card["joiningFeeAmount"] == card["annualFeeAmount"]
        assert "limited-period" in card["joiningFee"]
        assert any("₹50,000" in line for line in card["highlights"])
        assert any(url.startswith("https://www.tataneu.com/") for url in card["sourceUrls"])
        assert urlparse(card["applyUrl"]).hostname == "www.hdfc.bank.in"


def test_restricted_cards_do_not_enter_general_quiz_but_history_is_resolvable():
    restricted = [c for c in CARDS if c.get("recommendationEligible") is False]
    assert len(restricted) == 36
    for goal in ("shopping", "cashback", "travel", "fuel"):
        answers = profile()
        answers.update(goal=goal, fee="free", spend="vhigh", creditRoute="regular")
        assert recommend_cards(answers, restricted) == []
        historic = recommend_cards(answers, restricted, include_unavailable=True)
        assert {s["card"]["id"] for s in historic} == {c["id"] for c in restricted}
    # Older catalog/custom records without the new flag remain recommendable.
    ordinary = dict(CARDS[0])
    ordinary.pop("recommendationEligible", None)
    assert recommend_cards(profile(), [ordinary])[0]["card"]["id"] == ordinary["id"]


def test_expansion_preserves_existing_92_and_adds_distinct_products():
    # Freeze pre-expansion product facts while allowing sourced presentation assets.
    frozen = [
        {key: value for key, value in card.items() if key not in {"imageUrl", "imageSourceUrl"}}
        for card in CARDS[:92]
    ]
    encoded = json.dumps(frozen, sort_keys=True, ensure_ascii=False).encode()
    assert hashlib.sha256(encoded).hexdigest() == "6e01e1a527a591ddc0121b63ae9852da4884d6738292c65defb12bfc21dcbf8f"
    batch = [c for c in CARDS if c.get("catalogBatch") == "expansion-100-2026-10-09"]
    assert len(batch) == 100
    # A '+' distinguishes actual Plus tiers and must survive name normalization.
    names = ["".join(ch for ch in c["name"].lower().replace("+", "plus") if ch.isalnum()) for c in CARDS]
    assert len(names) == len(set(names))
    official_hosts = {"www.sbicard.com", "www.rbl.bank.in", "www.idfcfirst.bank.in",
                      "www.icici.bank.in", "www.indusind.bank.in", "www.hsbc.bank.in", "www.kotak.bank.in"}
    assert all(urlparse(c["applyUrl"]).hostname in official_hosts for c in batch)


def test_hdfc_personal_expansion_is_current_and_distinct():
    batch = [c for c in CARDS if c.get("catalogBatch") == "expansion-hdfc-18-2026-10-11"]
    assert len(batch) == 18
    assert all(c["issuer"] == "HDFC Bank" and c["applicationsOpen"] for c in batch)
    assert all(urlparse(c["applyUrl"]).hostname == "www.hdfc.bank.in" for c in batch)
    assert not any("business" in c["name"].lower() for c in batch)


def test_four_bank_personal_expansion_is_sourced_and_excludes_business_cards():
    batch = [c for c in CARDS if c.get("catalogBatch") == "expansion-pnb-bob-idbi-yes-34-2026-10-11"]
    assert len(batch) == 34
    assert {c["issuer"] for c in batch} == {"Punjab National Bank", "BOBCARD", "IDBI Bank", "YES BANK"}
    assert all(c["applicationsOpen"] and c["sourceUrls"] for c in batch)
    assert not any(any(word in c["name"].lower() for word in ("business", "corporate", "enterprise", "svanidhi")) for c in batch)
    expected_hosts = {"creditcard.pnb.bank.in", "www.bobcard.co.in", "www.idbibank.in", "www.yesbank.in"}
    assert all(urlparse(c["applyUrl"]).hostname in expected_hosts for c in batch)


def test_fintech_cobrand_expansion_names_the_regulated_issuer():
    batch = [c for c in CARDS if c.get("catalogBatch") == "expansion-fintech-cobrand-10-2026-10-11"]
    assert len(batch) == 10
    assert all(c.get("coBrandPartner") and c["issuer"] != c["coBrandPartner"] for c in batch)
    assert {c["coBrandPartner"] for c in batch} == {"Kredit.Pe", "SalarySe", "Zaggle", "OneCard", "Scapia", "Paisabazaar", "super.money"}
    assert all(c["applicationsOpen"] and c["active"] for c in batch)
    assert not any(any(term in c["name"].lower() for term in ("corporate", "prepaid", "business")) for c in batch)


def test_new_fee_and_currency_edge_cases():
    by_id = {c["id"]: c for c in CARDS}
    unnati = by_id["sbi-sbi-card-unnati"]
    assert unnati["secured"] and unnati["joiningFeeAmount"] == 0
    assert unnati["annualFeeAmount"] == 499 and unnati["feeType"] != "free"
    assert "year five" in unnati["annualFee"]
    cookies = by_id["rbl-cookies"]
    assert cookies["annualFeeAmount"] == 1200 and "per month" in cookies["annualFee"]
    cred = by_id["indusind-CRED-IndusInd-Bank-ruPay-credit-card"]
    assert cred["rewardCurrency"] == "CRED Reward Points" and "cashback" not in cred["bestFor"]
    assert any("₹0.50" in h for h in cred["highlights"])
    for suffix in ("plus", "infinity"):
        neu = by_id[f"sbi-tata-neu-{suffix}-sbi-card"]
        assert neu["rewardCurrency"] == "NeuCoins" and "cashback" not in neu["bestFor"]
