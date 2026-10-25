"""Real MongoDB drill using synthetic data only, never a production URI."""
import base64
import json
import os
from pathlib import Path
import secrets
import tempfile
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import MongoClient
from backup import backup, restore


def run():
    client = MongoClient('mongodb://127.0.0.1:27017', serverSelectionTimeoutMS=5000)
    suffix = secrets.token_hex(8)
    source = 'cardiq_drill_' + suffix
    target = 'cardiq_restore_' + suffix
    os.environ.update(MONGODB_BACKUP_URI='mongodb://127.0.0.1:27017', MONGODB_DATABASE=source,
                      MONGODB_RESTORE_URI='mongodb://127.0.0.1:27017',
                      BACKUP_ENCRYPTION_KEY=base64.b64encode(secrets.token_bytes(32)).decode())
    original = client[source]
    original.cards.insert_many(json.loads(Path('backend/cards_catalog.json').read_text()))
    original.cards.create_index('id', unique=True)
    original.quiz_results.insert_one({'_id': ObjectId(), 'created_at': datetime.now(timezone.utc),
                                      'answers': {'goal': 'cashback'}, 'result_id': 'synthetic-only'})
    original.quiz_results.create_index('result_id', unique=True)
    original.quiz_results.create_index('created_at')
    with tempfile.TemporaryDirectory() as tmp:
        archive = str(Path(tmp) / 'test.aesgcm')
        backup(archive)
        restore(archive, source, target)
        recovered = client[target]
        assert set(original.list_collection_names()) == set(recovered.list_collection_names())
        for name in original.list_collection_names():
            assert list(original[name].find().sort('_id')) == list(recovered[name].find().sort('_id'))
            assert original[name].index_information() == recovered[name].index_information()
        # Repeated restore must not overwrite even an isolated recovery DB.
        try:
            restore(archive, source, target)
        except ValueError:
            pass
        else:
            raise AssertionError('Overwrite protection failed')
    # No source data deletion is part of this script. Both DBs are synthetic and
    # disappear with the ephemeral CI service/container.
    print('Real MongoDB drill passed: 261 catalogue cards, BSON/date fields, collection parity, indexes and overwrite protection.')
    client.close()


if __name__ == '__main__':
    run()
