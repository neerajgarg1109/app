import asyncio
from datetime import datetime, timedelta, timezone
import importlib

import httpx
from mongomock_motor import AsyncMongoMockClient


def test_readiness_and_consented_runner_safety(monkeypatch):
    async def run():
        server = importlib.import_module('server')
        database = AsyncMongoMockClient()['isolated_operations']
        monkeypatch.setattr(server, 'db', database)
        monkeypatch.setenv('REMINDER_RUNNER_TOKEN', 'isolated-runner-token')
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url='http://test') as api:
            assert (await api.get('/api/ready')).status_code == 503
            await database.cards.insert_one(dict(server.CARDS[0]))
            ready = await api.get('/api/ready')
            assert ready.status_code == 200 and ready.headers['cache-control'] == 'no-store'
            async def unavailable(*args, **kwargs): raise RuntimeError('private-database-uri')
            original_command = database.command
            monkeypatch.setattr(database, 'command', unavailable)
            down = await api.get('/api/ready')
            assert down.status_code == 503 and 'private-database-uri' not in down.text
            monkeypatch.setattr(database, 'command', original_command)
            headers = {'X-Admin-Token': 'isolated-runner-token'}
            assert (await api.get('/api/admin/cards', headers=headers)).status_code == 401
            assert (await api.post('/api/admin/send-review-reminders?dry_run=true')).status_code == 401
            now = datetime.now(timezone.utc)
            for name, consent in [('consented', True), ('no-consent', False)]:
                await database.review_followups.insert_one({'followup_id': name, 'card_id': server.CARDS[0]['id'],
                    'email': name + '@example.com', 'due_at': now - timedelta(days=1),
                    'review_consent': consent, 'review_submitted': False, 'reminder_sent': False})
            sent = []
            async def delivery(**message):
                sent.append(message)
                await asyncio.sleep(.01)
                return 'synthetic-id'
            monkeypatch.setattr(server, 'send_email', delivery)
            dry = await api.post('/api/admin/send-review-reminders?dry_run=true', headers=headers)
            assert dry.json() == {'due': 1, 'sent': 0, 'dry_run': True, 'needs_review': 0} and not sent
            runs = await asyncio.gather(*(api.post('/api/admin/send-review-reminders', headers=headers) for _ in range(4)))
            assert all(r.status_code == 200 for r in runs) and len(sent) == 1
            assert sent[0]['to'] == 'consented@example.com'
            assert (await database.review_followups.find_one({'followup_id': 'no-consent'}))['reminder_sent'] is False
            await database.review_followups.insert_one({'followup_id': 'ambiguous', 'card_id': server.CARDS[0]['id'],
                'email': 'ambiguous@example.com', 'due_at': now, 'review_consent': True,
                'review_submitted': False, 'reminder_sent': False})
            async def ambiguous(**kwargs): raise TimeoutError('Provider may have accepted delivery')
            monkeypatch.setattr(server, 'send_email', ambiguous)
            await api.post('/api/admin/send-review-reminders', headers=headers)
            assert (await database.review_followups.find_one({'followup_id': 'ambiguous'}))['delivery_state'] == 'needs_review'
            assert (await api.post('/api/admin/send-review-reminders', headers=headers)).json()['due'] == 0
            assert (await api.post('/api/admin/send-review-reminders?dry_run=true', headers=headers)).json()['needs_review'] == 1
    asyncio.run(run())
