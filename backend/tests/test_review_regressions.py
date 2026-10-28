"""Concurrency and public-data regressions identified during the code review."""
import asyncio
import hashlib
import importlib
from datetime import datetime, timedelta, timezone
from copy import deepcopy
from types import SimpleNamespace

import httpx
from mongomock_motor import AsyncMongoMockClient


def test_public_cards_never_expose_drafts(monkeypatch):
    async def run():
        server = importlib.import_module('server')
        database = AsyncMongoMockClient()['review_public_cards']
        monkeypatch.setattr(server, 'db', database)
        card = deepcopy(server.CARDS[0])
        card.update(draft={'name': 'Unpublished secret', 'expectedPayout': 123}, adminManaged=True)
        await database.cards.insert_one(card)
        await database.cards.insert_one({'id': 'new-draft', 'active': False, 'publicationStatus': 'draft', 'draft': {'name': 'Secret'}})
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url='http://test') as api:
            for path in ['/api/cards', '/api/cards/' + card['id']]:
                response = await api.get(path)
                assert response.status_code == 200 and 'Unpublished secret' not in response.text
                assert 'expectedPayout' not in response.text and 'adminManaged' not in response.text
            assert (await api.get('/api/cards/new-draft')).status_code == 404
            compared = await api.post('/api/cards/compare', json={'ids': [card['id'], 'new-draft']})
            assert [c['id'] for c in compared.json()] == [card['id']]
            assert 'draft' not in compared.text
        assert (await database.cards.find_one({'id': card['id']}))['draft']['name'] == 'Unpublished secret'
    asyncio.run(run())


def test_one_invitation_accepts_only_one_concurrent_review(monkeypatch):
    async def run():
        server = importlib.import_module('server')
        database = AsyncMongoMockClient()['review_token_race']
        monkeypatch.setattr(server, 'db', database)
        await database.review_followups.insert_one({'followup_id': 'one', 'card_id': 'card', 'review_submitted': False,
            'token_hash': hashlib.sha256(b'one-use-token').hexdigest(),
            'token_expires_at': datetime.now(timezone.utc) + timedelta(days=1)})
        original_insert = database.cardholder_reviews.insert_one
        async def delayed_insert(review):
            await asyncio.sleep(.02)
            return await original_insert(review)
        reviews = database.cardholder_reviews
        monkeypatch.setattr(reviews, 'insert_one', delayed_insert)
        monkeypatch.setattr(server, 'db', SimpleNamespace(review_followups=database.review_followups, cardholder_reviews=reviews))
        payload = {key: 4 for key in ['overall', 'rewards', 'redemption', 'service', 'app_experience', 'acceptance']}
        payload.update(current_holder=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url='http://test') as api:
            results = await asyncio.gather(*(api.post('/api/reviews/invite/one-use-token', json=payload) for _ in range(5)))
            assert sorted(r.status_code for r in results) == [200, 404, 404, 404, 404]
        assert await database.cardholder_reviews.count_documents({}) == 1
    asyncio.run(run())


def test_concurrent_alert_campaign_sends_once_and_keeps_old_unsubscribe_links(monkeypatch):
    async def run():
        server = importlib.import_module('server')
        database = AsyncMongoMockClient()['review_alert_race']
        monkeypatch.setattr(server, 'db', database)
        monkeypatch.setattr(server, 'ADMIN_TOKEN', 'review-owner')
        card = deepcopy(server.CARDS[0])
        await database.cards.insert_one(card)
        token = 'previous-unsubscribe-link-token-12345678'
        await database.card_alert_subscriptions.insert_one({'subscription_id': 'one', 'status': 'active',
            'scope_type': 'all', 'email': 'synthetic@example.com', 'unsubscribe_token_hash': hashlib.sha256(token.encode()).hexdigest()})
        messages = []
        async def delivery(**message):
            messages.append(message)
            await asyncio.sleep(.02)
            return 'synthetic-message-id'
        monkeypatch.setattr(server, 'send_email', delivery)
        payload = {'card_id': card['id'], 'title': 'Verified fee update', 'summary': 'Check official fee terms.',
            'source_url': card['sourceUrls'][0], 'change_type': 'fee-change', 'idempotency_key': 'review-campaign-one'}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url='http://test') as api:
            results = await asyncio.gather(*(api.post('/api/admin/card-alerts/send', headers={'X-Admin-Token': 'review-owner'}, json=payload) for _ in range(5)))
            assert all(response.status_code == 200 for response in results), [(r.status_code, r.text) for r in results]
            assert len(messages) == 1
            result = await api.post('/api/card-alerts/unsubscribe', json={'token': token})
            assert result.status_code == 200
        assert (await database.card_alert_subscriptions.find_one({'subscription_id': 'one'}))['status'] == 'unsubscribed'
    asyncio.run(run())


def test_blank_environment_tokens_cannot_grant_admin_access(monkeypatch):
    server = importlib.import_module('server')
    for name in ['ADMIN_TOKEN', 'ADMIN_VIEWER_TOKEN', 'ADMIN_EDITOR_TOKEN', 'ADMIN_PUBLISHER_TOKEN']:
        monkeypatch.setattr(server, name, '')
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as failure:
        server._require_admin('')
    assert failure.value.status_code == 401


def test_current_analytics_unique_index_survives_restarts(monkeypatch):
    async def run():
        server = importlib.import_module('server')
        database = AsyncMongoMockClient()['review_index_restart']
        monkeypatch.setattr(server, 'db', database)
        await server._ensure_product_event_index()
        async def must_not_drop(*args, **kwargs):
            raise AssertionError('Current unique index must not be dropped during restart')
        events = database.product_events
        monkeypatch.setattr(events, 'drop_index', must_not_drop)
        monkeypatch.setattr(server, 'db', SimpleNamespace(product_events=events))
        await server._ensure_product_event_index()
        index = (await database.product_events.index_information())['unique_product_funnel_event']
        assert index['unique'] is True
    asyncio.run(run())


def test_ambiguous_review_insert_does_not_reenable_invitation(monkeypatch):
    async def run():
        server = importlib.import_module('server')
        database = AsyncMongoMockClient()['review_ambiguous_insert']
        monkeypatch.setattr(server, 'db', database)
        token_hash = hashlib.sha256(b'ambiguous-token').hexdigest()
        await database.review_followups.insert_one({'followup_id': 'one', 'card_id': 'card', 'review_submitted': False,
            'token_hash': token_hash, 'token_expires_at': datetime.now(timezone.utc) + timedelta(days=1)})
        insert = database.cardholder_reviews.insert_one
        async def uncertain_insert(review):
            await insert(review)
            raise TimeoutError('Acknowledgement lost')
        reviews = database.cardholder_reviews
        monkeypatch.setattr(reviews, 'insert_one', uncertain_insert)
        monkeypatch.setattr(server, 'db', SimpleNamespace(review_followups=database.review_followups, cardholder_reviews=reviews))
        payload = {key: 4 for key in ['overall', 'rewards', 'redemption', 'service', 'app_experience', 'acceptance']}
        payload['current_holder'] = True
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url='http://test') as api:
            assert (await api.post('/api/reviews/invite/ambiguous-token', json=payload)).status_code == 503
            assert (await api.post('/api/reviews/invite/ambiguous-token', json=payload)).status_code == 404
        assert await database.cardholder_reviews.count_documents({}) == 1
        assert (await database.review_followups.find_one({'followup_id': 'one'}))['review_submission_state'] == 'needs_review'
    asyncio.run(run())


def test_abandoned_quiz_reminders_require_explicit_consent(monkeypatch):
    async def run():
        server = importlib.import_module('server')
        database = AsyncMongoMockClient()['review_reminder_consent']
        monkeypatch.setattr(server, 'db', database)
        monkeypatch.setattr(server, 'ADMIN_TOKEN', 'review-owner')
        deliveries = []
        async def send(**message):
            deliveries.append(message)
        monkeypatch.setattr(server, 'send_email', send)
        await database.partial_sessions.insert_one({'email': 'legacy@example.com', 'completed': False})
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url='http://test') as api:
            for consent in [False, True]:
                response = await api.post('/api/quiz/partial', json={'email': ('yes' if consent else 'no') + '@example.com', 'reminder_consent': consent})
                assert response.status_code == 200
            response = await api.post('/api/admin/send-reminders', headers={'X-Admin-Token': 'review-owner'})
            assert response.json()['reminders_sent'] == 1
        assert [message['to'] for message in deliveries] == ['yes@example.com']
    asyncio.run(run())
