import asyncio
import importlib
import io

import httpx
import pytest
from PIL import Image
from mongomock_motor import AsyncMongoMockClient

from card_images import normalize_card_image, validate_card_image_url, MAX_IMAGE_BYTES


def png(size=(240, 152)):
    output = io.BytesIO()
    Image.new("RGBA", size, (255, 0, 0, 128)).save(output, "PNG")
    return output.getvalue()


def test_image_validation_and_normalization():
    result = normalize_card_image(png())
    with Image.open(io.BytesIO(result)) as image:
        assert image.format == "WEBP"
        assert image.size == (240, 152)
        assert image.getpixel((0, 0))[3] == 128
    for invalid in [b'<svg><script>alert(1)</script></svg>', b'not-an-image', png((20, 20)), b'x' * (MAX_IMAGE_BYTES + 1)]:
        with pytest.raises(ValueError):
            normalize_card_image(invalid)
    assert validate_card_image_url('/cards/official.webp') == '/cards/official.webp'
    assert validate_card_image_url('https://api.example/api/card-images/abc')
    for url in ['javascript:alert(1)', '//untrusted.example/x', '/cards/../secret', 'https://user:password@host/card.png']:
        with pytest.raises(ValueError):
            validate_card_image_url(url)


def test_upload_permissions_storage_and_draft_publish(monkeypatch):
    monkeypatch.setenv('MONGO_URL', 'mongodb://127.0.0.1:27017')
    monkeypatch.setenv('DB_NAME', 'cardiq_image_tests')
    server = importlib.import_module('server')
    monkeypatch.setattr(server, 'db', AsyncMongoMockClient()['cardiq_image_tests'])
    monkeypatch.setattr(server, 'ADMIN_EDITOR_TOKEN', 'image-editor')
    monkeypatch.setattr(server, 'ADMIN_PUBLISHER_TOKEN', 'image-publisher')
    monkeypatch.setattr(server, 'ADMIN_VIEWER_TOKEN', 'image-viewer')

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url='https://api.example') as client:
            assert (await client.post('/api/admin/card-images', content=png())).status_code == 401
            assert (await client.post('/api/admin/card-images', content=png(), headers={'X-Admin-Token': 'image-viewer'})).status_code == 403
            headers = {'X-Admin-Token': 'image-editor'}
            response = await client.post('/api/admin/card-images', content=png(), headers=headers)
            assert response.status_code == 200, response.text
            path = response.json()['path']
            duplicate = await client.post('/api/admin/card-images', content=png(), headers=headers)
            assert duplicate.json()['path'] == path
            assert await server.db.card_images.count_documents({}) == 1
            asset = await client.get(path)
            assert asset.status_code == 200
            assert asset.headers['content-type'] == 'image/webp'
            assert 'immutable' in asset.headers['cache-control']
            assert (await client.get('/api/card-images/not-an-id')).status_code == 404
            assert (await client.post('/api/admin/card-images', content=b'<svg/>', headers=headers)).status_code == 422
            assert (await client.post('/api/admin/card-images', content=b'x' * (MAX_IMAGE_BYTES + 1), headers=headers)).status_code == 413
            card = {'id': 'test-image', 'name': 'Image Card', 'issuer': 'Test Bank', 'rewardLine': 'Rewards', 'applyUrl': 'https://issuer.example/card', 'imageUrl': '/cards/old.webp', 'active': True, 'applicationsOpen': True, 'publicationStatus': 'published'}
            await server.db.cards.insert_one(dict(card))
            payload = {**card, 'imageUrl': 'https://api.example' + path}
            response = await client.put('/api/admin/cards/test-image', json=payload, headers=headers)
            assert response.status_code == 200, response.text
            stored = await server.db.cards.find_one({'id': card['id']})
            assert stored['imageUrl'] == '/cards/old.webp'
            assert stored['draft']['imageUrl'] == payload['imageUrl']
            assert (await client.post('/api/admin/cards/test-image/publish', headers={'X-Admin-Token': 'image-publisher'})).status_code == 200
            public = await client.get('/api/cards/test-image')
            assert public.json()['imageUrl'] == payload['imageUrl']
            history = await server.db.card_versions.find_one({'card_id': card['id']})
            assert history['snapshot']['imageUrl'] == '/cards/old.webp'
            assert (await client.get(path)).status_code == 200
    asyncio.run(run())
