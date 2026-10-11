"""One caller-managed job, draining ready/health/result frames.

Offline process demonstration (empty inventory; no Telegram):
    python examples/reading_worker.py --demo

Read with an already provisioned inventory and logged-in session:
    python examples/reading_worker.py --config worker.json --account 123456789 \
        --target @example_group --after-id 100 --limit 20

This prints results; it does not persist messages, move a cursor or retry a job.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tgdata import ReadBudget
from tgdata.worker_protocol import MAX_RESPONSE_BYTES, RequestDecoder


def read_frame(stream):
    raw = stream.readline(MAX_RESPONSE_BYTES + 1)
    if not raw or len(raw) > MAX_RESPONSE_BYTES or not raw.endswith(b'\n'):
        raise RuntimeError('No complete worker reply; job completion is unknown')
    value = json.loads(raw)
    if value.get('version') != 1:
        raise RuntimeError('Unsupported worker protocol')
    return value


def run(config, request):
    raw = (json.dumps(request) + '\n').encode('utf-8')
    RequestDecoder().decode(raw)  # Catch caller mistakes before starting a job.
    process = subprocess.Popen([sys.executable, '-m', 'tgdata.worker', '--config', str(config)],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    terminal = None
    try:
        ready = read_frame(process.stdout)
        if ready['kind'] != 'ready':
            raise RuntimeError('Worker refused startup: ' + ready['error']['type'])
        print('Ready:', ready['worker_id'], 'accounts:', ready['account_count'])
        process.stdin.write(raw)
        process.stdin.flush()
        while terminal is None:
            frame = read_frame(process.stdout)
            if (frame.get('instance_id') != ready['instance_id']
                    or frame.get('request_id') != request['request_id']):
                raise RuntimeError('Worker reply correlation failed')
            if frame['kind'] == 'health':
                print('Health:', json.dumps(frame['event']))
            elif frame['kind'] == 'result':
                terminal = frame
            else:
                raise RuntimeError('Unexpected worker reply')
        print(json.dumps(terminal, indent=2, ensure_ascii=False))
    finally:
        process.stdin.close()
        if terminal is None and process.poll() is None:
            process.terminate()
        # Graceful termination waits for native cleanup. The application decides
        # whether and when to force-kill a stuck process and accept uncertainty.
        code = process.wait()
        process.stdout.close()
    if code not in (0, 3) or (code == 3 and not terminal['worker_stopping']):
        raise RuntimeError('Worker stopped unexpectedly; do not retry automatically')
    return terminal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--account')
    parser.add_argument('--target')
    parser.add_argument('--operation', choices=('read_batch', 'lookup_group',
                        'check_group_access', 'join_group'), default='read_batch')
    parser.add_argument('--after-id', default='0')
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    if args.demo:
        with tempfile.TemporaryDirectory(prefix='tgdata_worker_demo_') as directory:
            root = Path(directory)
            ReadBudget(root / 'read.sqlite3')  # New empty demo ledger only.
            config = root / 'worker.json'
            config.write_text(json.dumps(dict(version=1, worker_id='offline-demo',
                read_budget='read.sqlite3', accounts=[])))
            result = run(config, dict(version=1, request_id=1, account_id='111',
                operation='lookup_group', params=dict(target='@synthetic_room')))
            assert result['error']['code'] == 'unknown_account'
            print('Offline demo complete: ready, local refusal, EOF. No account was opened.')
        return
    if args.config is None or args.account is None or args.target is None:
        parser.error('normal use requires --config, --account and --target')
    params = dict(group_id=args.target, after_id=args.after_id, limit=args.limit) \
        if args.operation == 'read_batch' else dict(target=args.target)
    run(args.config, dict(version=1, request_id=1, account_id=args.account,
                         operation=args.operation, params=params))


if __name__ == '__main__':
    main()
