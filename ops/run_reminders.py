"""Run only explicitly consented review reminders; never incomplete-quiz campaigns."""
import json
import os
import sys
import urllib.request
from urllib.parse import urlparse


def run():
    origin = os.environ.get('CARDIQ_API_URL', 'https://api.findmybest.cards').rstrip('/')
    if urlparse(origin).scheme != 'https' or urlparse(origin).netloc != 'api.findmybest.cards':
        raise ValueError('Reminder runner requires the production API origin')
    token = os.environ['REMINDER_RUNNER_TOKEN']
    if not token:
        raise ValueError('Missing runner token')
    dry_run = os.environ.get('CARDIQ_REMINDERS_SEND', 'false') != 'true'
    preflight = urllib.request.Request(origin + '/api/admin/send-review-reminders?dry_run=true',
                                     data=b'', method='POST', headers={'X-Admin-Token': token})
    with urllib.request.urlopen(preflight, timeout=30) as response:
        summary = json.load(response)
    if summary.get('needs_review', 0):
        raise RuntimeError('Ambiguous deliveries require human review before sending')
    request = urllib.request.Request(origin + '/api/admin/send-review-reminders?dry_run=' + str(dry_run).lower(),
                                     data=b'', method='POST', headers={'X-Admin-Token': token})
    # No retries: an ambiguous delivery outcome requires human investigation.
    with urllib.request.urlopen(request, timeout=600) as response:
        result = json.load(response)
    if not isinstance(result.get('due'), int) or not isinstance(result.get('sent'), int):
        raise RuntimeError('Invalid runner response')
    if not dry_run and result['due'] != result['sent']:
        raise RuntimeError('A claimed reminder needs manual delivery review')
    print(json.dumps({key: result[key] for key in ['due', 'sent']} | {'dry_run': dry_run}))


if __name__ == '__main__':
    try:
        run()
    except Exception as error:
        print('Reminder runner failed: ' + type(error).__name__, file=sys.stderr)
        sys.exit(1)
