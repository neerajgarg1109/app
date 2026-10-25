import secrets
import unittest
from unittest.mock import patch

from cryptography.exceptions import InvalidTag
from ops.backup import encrypt, decrypt, local_restore_only, MAGIC
from ops.monitor import check


class BackupSafety(unittest.TestCase):
    def test_round_trip_and_tampering(self):
        key = secrets.token_bytes(32)
        data = b'synthetic BSON archive' * 200
        encrypted = encrypt(data, key)
        self.assertNotIn(data, encrypted)
        self.assertEqual(decrypt(encrypted, key), data)
        with self.assertRaises(InvalidTag): decrypt(encrypted, secrets.token_bytes(32))
        corrupted = encrypted[:-1] + bytes([encrypted[-1] ^ 1])
        with self.assertRaises(InvalidTag): decrypt(corrupted, key)
        self.assertNotEqual(encrypt(data, key), encrypted)

    def test_no_remote_or_production_restore(self):
        local_restore_only('mongodb://127.0.0.1:27017', 'cardiq_restore_test')
        for uri in ['mongodb+srv://production.example', 'mongodb://production.example',
                    'mongodb://localhost,production.example', 'mongodb://localhost/?tls=false',
                    'mongodb://user:pass@localhost', 'mongodb://localhost/production']:
            with self.subTest(uri=uri), self.assertRaises(ValueError):
                local_restore_only(uri, 'cardiq_restore_test')
        with self.assertRaises(ValueError): local_restore_only('mongodb://localhost', 'cardiq_prod')

    def test_bad_header(self):
        with self.assertRaises(ValueError): decrypt(b'not a backup', secrets.token_bytes(32))


class MonitorSafety(unittest.TestCase):
    @patch('ops.monitor.fetch')
    def test_detects_missing_assets(self, fetch):
        fetch.return_value = b'<html>broken deployment</html>'
        with self.assertRaises(RuntimeError): check('https://example.com', 'https://api.example.com')

    @patch('ops.monitor.fetch')
    def test_detects_database_unavailable(self, fetch):
        fetch.side_effect = [b'<script src="/static/js/main.js"></script>', b'js', b'{"status":"down"}']
        with self.assertRaises(RuntimeError): check('https://example.com', 'https://api.example.com')

    @patch('ops.monitor.fetch')
    def test_success_and_tls(self, fetch):
        fetch.side_effect = [b'<script src="/static/js/main.js"></script>', b'js', b'{"status":"ready"}', b'[{"id":"one"}]']
        check('https://example.com', 'https://api.example.com')
        with self.assertRaises(ValueError): check('http://example.com', 'https://api.example.com')


if __name__ == '__main__': unittest.main()
