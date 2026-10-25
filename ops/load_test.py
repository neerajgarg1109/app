"""50-user sustained workload, restricted to an isolated loopback API."""
import argparse
import asyncio
import json
from pathlib import Path
import statistics
import time
from urllib.parse import urlparse

import httpx


async def run(origin, users, duration, output):
    parsed = urlparse(origin)
    if parsed.scheme != 'http' or parsed.hostname not in {'localhost', '127.0.0.1'} or parsed.query or parsed.username:
        raise ValueError('Load tests are restricted to a local isolated API')
    if not 1 <= users <= 100 or not 10 <= duration <= 300:
        raise ValueError('Use 1–100 users for 10–300 seconds')
    rows = []
    deadline = time.monotonic() + duration
    async with httpx.AsyncClient(base_url=origin, timeout=15, limits=httpx.Limits(max_connections=users, max_keepalive_connections=users)) as client:
        async def user(number):
            turn = 0
            while time.monotonic() < deadline:
                kind = (turn + number) % 5
                started = time.monotonic()
                try:
                    if kind < 3:
                        r = await client.post('/api/quiz/submit', json={'answers': {
                            'goal': ['travel', 'cashback', 'shopping'][kind], 'spend': 'mid', 'fee': 'worth',
                            'usage': 'online', 'priority': 'rewards', 'creditRoute': 'regular'}})
                        value = r.json(); valid = bool(value.get('result_id') and value.get('scored'))
                        if valid:
                            saved = await client.get('/api/results/' + value['result_id'])
                            valid = saved.status_code == 200 and saved.json().get('result_id') == value['result_id']
                    elif kind == 3:
                        r = await client.post('/api/tools/value-calculator', json={'online': 10000, 'other': 15000})
                        valid = bool(r.json().get('results'))
                    else:
                        r = await client.get('/api/cards?view=summary')
                        valid = isinstance(r.json(), list) and len(r.json()) == 261
                    rows.append({'ms': round((time.monotonic()-started)*1000), 'ok': r.status_code == 200 and valid, 'kind': kind})
                except (httpx.HTTPError, ValueError):
                    rows.append({'ms': round((time.monotonic()-started)*1000), 'ok': False, 'kind': kind})
                turn += 1
                await asyncio.sleep(1)  # Closed-loop users with one-second think time.
        await asyncio.gather(*(user(i) for i in range(users)))
    times = sorted(r['ms'] for r in rows)
    report = {'concurrent_users': users, 'duration_seconds': duration, 'journeys': len(rows),
              'failures': sum(not r['ok'] for r in rows), 'median_ms': round(statistics.median(times)),
              'p95_ms': times[int((len(times)-1)*.95)], 'max_ms': max(times),
              'scope': 'Isolated API; synthetic MongoDB; one-second think time; quiz journey includes save/readback. Not production Atlas or geography.'}
    Path(output).write_text(json.dumps(report, indent=2))
    print(json.dumps(report))
    if report['failures'] or report['p95_ms'] > 2000:
        raise RuntimeError('50-user target failed: requires zero errors and P95 <= 2 seconds')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--origin', default='http://127.0.0.1:8080'); p.add_argument('--users', type=int, default=50); p.add_argument('--seconds', type=int, default=60); p.add_argument('--output', default='load-report.json'); args = p.parse_args()
    asyncio.run(run(args.origin, args.users, args.seconds, args.output))
