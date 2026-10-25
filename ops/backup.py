"""Encrypt logical MongoDB archives; restore only to a loopback-only isolated DB.

No URI, document or tool stderr is logged. mongodump preserves BSON and indexes.
A logical dump of an active Free cluster is NOT a point-in-time snapshot.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
from urllib.parse import urlparse

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b'CARDIQ-BACKUP-1\n'


def key_from_environment():
    value = base64.b64decode(os.environ['BACKUP_ENCRYPTION_KEY'], validate=True)
    if len(value) != 32:
        raise ValueError('Encryption key must be 32 random bytes in base64')
    return value


def encrypt(data, key):
    nonce = secrets.token_bytes(12)
    return MAGIC + nonce + AESGCM(key).encrypt(nonce, data, MAGIC)


def decrypt(data, key):
    if not data.startswith(MAGIC):
        raise ValueError('Invalid backup format')
    start = len(MAGIC)
    return AESGCM(key).decrypt(data[start:start+12], data[start+12:], MAGIC)


def database_name(value):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,63}', value):
        raise ValueError('Invalid database name')
    return value


def local_restore_only(uri, target):
    parsed = urlparse(uri)
    # Do not accept SRV, credentials, multiple hosts, query-string overrides or
    # any remote restore destination. No --drop is used, even in the drill.
    if (parsed.scheme != 'mongodb' or parsed.hostname not in {'localhost', '127.0.0.1'}
            or parsed.username or parsed.password or parsed.query or ',' in parsed.netloc
            or parsed.path not in {'', '/'}):
        raise ValueError('Restoration is restricted to a local isolated MongoDB')
    database_name(target)
    if not target.startswith('cardiq_restore_'):
        raise ValueError('Restore target must start with cardiq_restore_')


def tool_run(command):
    result = subprocess.run(command, capture_output=True, timeout=600)
    if result.returncode:
        raise RuntimeError('MongoDB archive command failed; inspect credentials/network privately')


def backup(output):
    uri = os.environ['MONGODB_BACKUP_URI']
    name = database_name(os.environ['MONGODB_DATABASE'])
    key = key_from_environment()  # Fail before generating plaintext if key is absent.
    from pymongo import MongoClient
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    try:
        if client[name].cards.find_one({}, {"_id": 1}) is None:
            raise ValueError('Source database has no CardIQ catalogue; refusing an empty or wrong-database backup')
    finally:
        client.close()
    output = Path(output)
    if output.exists():
        raise ValueError('Output already exists')
    with tempfile.TemporaryDirectory() as tmp:
        config = Path(tmp) / 'config.yml'
        config.write_text('uri: ' + json.dumps(uri))
        config.chmod(0o600)
        archive = Path(tmp) / 'dump.gz'
        tool_run(['mongodump', '--config=' + str(config), '--db=' + name,
                  '--archive=' + str(archive), '--gzip', '--numParallelCollections=1'])
        data = archive.read_bytes()
        if not data:
            raise RuntimeError('Empty backup archive')
        with output.open('xb') as destination:
            destination.write(encrypt(data, key))
        output.chmod(0o600)
    print('Encrypted database archive created. No plaintext artifact uploaded.')


def restore(archive, source, target):
    uri = os.environ.get('MONGODB_RESTORE_URI', 'mongodb://127.0.0.1:27017')
    local_restore_only(uri, target)
    source = database_name(source)
    from pymongo import MongoClient
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    if target in client.list_database_names():
        raise ValueError('Refusing to overwrite an existing restore database')
    plaintext = decrypt(Path(archive).read_bytes(), key_from_environment())
    with tempfile.TemporaryDirectory() as tmp:
        decrypted = Path(tmp) / 'restore.gz'
        decrypted.write_bytes(plaintext)
        decrypted.chmod(0o600)
        tool_run(['mongorestore', '--uri=' + uri, '--archive=' + str(decrypted), '--gzip',
                  '--nsInclude=' + source + '.*', '--nsFrom=' + source + '.*',
                  '--nsTo=' + target + '.*', '--stopOnError'])
    client.close()
    print('Archive restored to isolated local database. Verify documents and indexes before recovery sign-off.')


if __name__ == '__main__':
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('backup'); p.add_argument('--output', required=True)
    p = sub.add_parser('restore'); p.add_argument('--archive', required=True); p.add_argument('--source', required=True); p.add_argument('--target', required=True)
    args = parser.parse_args()
    try:
        if args.mode == 'backup': backup(args.output)
        else: restore(args.archive, args.source, args.target)
    except Exception as error:
        # Tool diagnostics and connection exceptions can contain credentials.
        print('Backup operation failed: ' + type(error).__name__)
        raise SystemExit(1)
