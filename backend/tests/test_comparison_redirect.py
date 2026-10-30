import asyncio
import importlib
from urllib.parse import urlparse, parse_qs

import httpx
from mongomock_motor import AsyncMongoMockClient


def test_comparison_redirect_preserves_attribution_and_falls_back(monkeypatch):
    monkeypatch.setenv('MONGO_URL','mongodb://localhost:27017')
    monkeypatch.setenv('DB_NAME','comparison_redirect_test')
    server=importlib.import_module('server')
    monkeypatch.setattr(server,'db',AsyncMongoMockClient()['comparison_redirect_test'])
    async def run():
        card={'id':'compare-card','name':'Card','issuer':'Issuer','active':True,'applicationsOpen':True,'applyUrl':'https://issuer.example/card','applyUrlOverride':'https://partner.example/apply?campaign=keep&subid=original','applyLinkStatus':'live'}
        await server.db.cards.insert_one(dict(card))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app),base_url='https://api.example',follow_redirects=False) as client:
            response=await client.get('/api/go/compare-card?subid=verdict_box_card_a&pair=sbi-cashback-vs-hdfc-millennia')
            assert response.status_code==302
            params=parse_qs(urlparse(response.headers['location']).query)
            assert params['campaign']==['keep']
            assert params['subid']==['original']
            assert params['cardiq_subid']==['verdict_box_card_a']
            event=await server.db.apply_events.find_one({'card_id':card['id']})
            assert event['placement_id']=='verdict_box_card_a'
            assert event['comparison_slug']=='sbi-cashback-vs-hdfc-millennia'
            assert event['link_type']=='partner'
            response=await client.get('/api/go/compare-card?subid=list_card&source=best-cashback-credit-cards-india')
            assert response.status_code==302
            assert parse_qs(urlparse(response.headers['location']).query)['source']==['best-cashback-credit-cards-india']
            event=await server.db.apply_events.find_one({'placement_id':'list_card'})
            assert event['source_page']=='best-cashback-credit-cards-india'
            assert (await client.get('/api/go/compare-card?subid=list_card&source=https://evil.example')).status_code==422
            await server.db.cards.update_one({'id':card['id']},{'$set':{'applyLinkStatus':'paused'}})
            response=await client.get('/api/go/compare-card?subid=calculator_winner_cta&pair=test-pair&url=https://evil.example')
            assert response.headers['location']=='https://issuer.example/card'
            assert (await client.get('/api/go/compare-card?subid=unknown')).status_code==422
            assert (await client.get('/api/go/compare-card?pair=https://evil.example')).status_code==422
            assert (await client.get('/api/go/missing')).status_code==404
            await server.db.cards.update_one({'id':card['id']},{'$set':{'applicationsOpen':False}})
            assert (await client.get('/api/go/compare-card')).status_code==409
    asyncio.run(run())
