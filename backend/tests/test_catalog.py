"""Catalog and migration regression tests; integration uses a disposable local DB."""
import asyncio
import importlib
import hashlib
import json
import os
import uuid
from copy import deepcopy
from urllib.parse import urlparse

import httpx
from motor.motor_asyncio import AsyncIOMotorClient

from cards_seed import CARDS, CATALOG_QUERY, DEMO_IDS, recommend_cards, seed_cards


def available_cards():
    return [c for c in CARDS if c.get("active") is not False
            and c.get("applicationsOpen") is not False
            and c.get("recommendationEligible") is not False]


def profile(**overrides):
    return dict(goal="travel", usage="flights", priority="lounge", fee="premium",
                spend="high", credit="excellent", international="often", **overrides)


def test_catalog_has_192_sourced_unique_real_cards():
    assert len(CARDS) == len({c["id"] for c in CARDS}) == 192
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


def test_international_travel_reason_does_not_invent_low_forex():
    atlas = next(c for c in CARDS if c["id"] == "axis-axis-bank-atlas-credit-card")
    reasons = recommend_cards(profile(), [atlas])[0]["reasons"]
    assert "Travel rewards suit your overseas purchases" in reasons
    assert not any("forex" in reason.lower() for reason in reasons)


def test_secured_options_and_free_fee_profiles():
    answers = profile()
    answers.update(credit="new", fee="free", priority="forex", usage="online", spend="low")
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
                response = await api.get("/api/cards")
                assert response.status_code == 200 and len(response.json()) == len(CARDS)
                restricted_ids = {c["id"] for c in CARDS if c.get("recommendationEligible") is False}
                assert restricted_ids <= {c["id"] for c in response.json()}
                ids = [CARDS[-1]["id"], CARDS[0]["id"]]
                response = await api.post("/api/cards/compare", json={"ids": ids})
                assert [c["id"] for c in response.json()] == ids
                assert (await api.get("/api/cards/missing-card")).status_code == 404
                response = await api.post("/api/quiz/submit", json={"answers": profile(),
                    "lead": {"name": "Catalog test", "email": "local-test@example.com"}})
                assert response.status_code == 200, response.text
                result = response.json()
                assert len(result["scored"]) == len(available_cards())
                assert not restricted_ids & {s["card"]["id"] for s in result["scored"]}
                # Updates must not rewrite a previously shared recommendation or email.
                top = result["scored"][0]["card"]
                await database.cards.update_one({"id": top["id"]}, {"$set": {"name": "Updated issuer name", "active": False}})
                saved = await api.get("/api/results/" + result["result_id"])
                assert saved.json() == result
                doc = await database.quiz_results.find_one({"result_id": result["result_id"]})
                assert (await server.scored_result(doc))[0]["card"]["name"] == top["name"]
                await database.quiz_results.insert_one({"result_id": "legacy", "answers": profile(), "scored_ids": [demo["id"]]})
                legacy = await api.get("/api/results/legacy")
                assert legacy.status_code == 200
                assert legacy.json()["scored"][0]["card"]["name"] == "Historical demo"
                assert (await api.get("/api/admin/leads")).status_code == 401
                # Catalog growth must not truncate legacy rankings or admin names
                # at the former 100-card cursor limit.
                await database.quiz_results.insert_one({"result_id": "expanded-legacy",
                    "answers": profile(), "scored_ids": [c["id"] for c in CARDS],
                    "recommended_card_id": CARDS[-1]["id"]})
                await database.leads.insert_one({"lead_id": "expanded-lead", "name": "Expanded catalog",
                    "email": "expanded@example.com", "result_id": "expanded-legacy"})
                expanded = await api.get("/api/results/expanded-legacy")
                assert len(expanded.json()["scored"]) == len(CARDS)
                headers = {"X-Admin-Token": server.ADMIN_TOKEN}
                leads = (await api.get("/api/admin/leads", headers=headers)).json()["leads"]
                assert next(l for l in leads if l["result_id"] == "expanded-legacy")["recommended_card"] == CARDS[-1]["name"]
                csv = await api.get("/api/admin/leads.csv", headers=headers)
                assert csv.status_code == 200 and CARDS[-1]["name"] in csv.text
                insights = await api.get("/api/admin/insights", headers=headers)
                assert insights.status_code == 200 and CARDS[-1]["name"] in insights.text
        finally:
            await client.drop_database(name)
            client.close()
    asyncio.run(run())


def test_hdfc_partner_sources_and_reward_currency():
    hdfc = [c for c in CARDS if c["issuer"] == "HDFC Bank"]
    assert len(hdfc) == 2
    assert {c["annualFeeAmount"] for c in hdfc} == {499, 1499}
    for card in hdfc:
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
    assert len(restricted) == 33
    for goal in ("shopping", "cashback", "travel", "fuel"):
        answers = profile()
        answers.update(goal=goal, fee="free", spend="vhigh", credit="excellent")
        assert recommend_cards(answers, restricted) == []
        historic = recommend_cards(answers, restricted, include_unavailable=True)
        assert {s["card"]["id"] for s in historic} == {c["id"] for c in restricted}
    # Older catalog/custom records without the new flag remain recommendable.
    ordinary = dict(CARDS[0])
    ordinary.pop("recommendationEligible", None)
    assert recommend_cards(profile(), [ordinary])[0]["card"]["id"] == ordinary["id"]


def test_expansion_preserves_existing_92_and_adds_distinct_products():
    # Freeze the pre-expansion records so additions cannot silently rewrite history.
    encoded = json.dumps(CARDS[:92], sort_keys=True, ensure_ascii=False).encode()
    assert hashlib.sha256(encoded).hexdigest() == "6e01e1a527a591ddc0121b63ae9852da4884d6738292c65defb12bfc21dcbf8f"
    batch = [c for c in CARDS if c.get("catalogBatch") == "expansion-100-2026-10-09"]
    assert len(batch) == 100
    # A '+' distinguishes actual Plus tiers and must survive name normalization.
    names = ["".join(ch for ch in c["name"].lower().replace("+", "plus") if ch.isalnum()) for c in CARDS]
    assert len(names) == len(set(names))
    official_hosts = {"www.sbicard.com", "www.rbl.bank.in", "www.idfcfirst.bank.in",
                      "www.icici.bank.in", "www.indusind.bank.in", "www.hsbc.bank.in", "www.kotak.bank.in"}
    assert all(urlparse(c["applyUrl"]).hostname in official_hosts for c in batch)


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
