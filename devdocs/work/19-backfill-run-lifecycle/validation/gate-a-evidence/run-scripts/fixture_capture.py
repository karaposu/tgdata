"""One-off Gate A fixture qualification; direct descending RPCs, never the tested reader."""
import argparse
import asyncio
from datetime import datetime, timezone
import importlib.util
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import time
import traceback

REPO = Path('/private/tmp/tgdata-19-backfill-run-lifecycle')
ROOT = Path('/private/tmp/tgdata19-gate-a-live-20261007')
sys.path.insert(0, str(REPO))
spec = importlib.util.spec_from_file_location('gate_probe', REPO / 'devdocs/work/19-backfill-run-lifecycle/live_probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
from telethon import functions, types, utils
from tgdata import TgData, ReadBudget

USERNAME = 'programlama_sohbet'
CONFIG = Path('/Users/ns/Desktop/projects/telegram-group-scraper/config.ini')
LEDGER = ROOT / 'account-read-budget.sqlite3'
CAP = 5000


class FixtureGuard(probe.ReadOnlyGuard):
    def __init__(self):
        super().__init__(-1, dict(max_rpc_requests=70, max_history_requests=6,
                                 max_requested_slots=600, max_media_bytes=0))
        self.resolutions = 0

    def before_send(self, request):
        raw = request
        for _ in range(9):
            if not isinstance(raw, probe._WRAPPERS):
                break
            raw = raw.query
        else:
            raise probe.ProbeStop('wrapper_depth')
        if isinstance(raw, functions.contacts.ResolveUsernameRequest):
            probe.require(raw.username.casefold() == USERNAME.casefold(), 'wrong_fixture_username')
            probe.require(self.resolutions < 2 and len(self.rpc) < self.limits['max_rpc_requests'], 'resolve_cap')
            self.resolutions += 1
            entry = dict(kind=type(raw).__name__, sent_at=probe._encode_date(datetime.now(timezone.utc)),
                         monotonic=time.monotonic(), outcome='pending', turn=0, page=None)
            self.rpc.append(entry)
            return entry
        return super().before_send(request)


def save(path, value):
    with Path(path).open('x', encoding='utf8') as output:
        json.dump(value, output, indent=2, sort_keys=True, allow_nan=False)
        output.write('\n')


async def capture(output):
    probe.require(probe.telethon.__version__ == '1.45.0', 'unsupported_sdk')
    budget = ReadBudget(LEDGER)
    guard = FixtureGuard()
    report = dict(kind='independent direct descending GetHistory fixture qualification',
                  selected_username=USERNAME, captured_at=probe._encode_date(datetime.now(timezone.utc)),
                  product_revision='23ceab53104e7e417c5cf93b62e0f7b71edfbe9e',
                  probe_sha256=hashlib.sha256((REPO / 'devdocs/work/19-backfill-run-lifecycle/live_probe.py').read_bytes()).hexdigest(),
                  budget_cap=CAP, gate_verdict='INCONCLUSIVE', messages=[])
    tg = TgData(str(CONFIG), connection_pool_size=1, interactive_login=False, read_budget=budget)
    factory = tg.connection_engine._new_client

    def instrumented(*args, **kwargs):
        client = factory(*args, **kwargs)
        guard.instrument(client)
        client.flood_sleep_threshold = 0
        client._request_retries = 0
        client._connection_retries = 1
        return client

    tg.connection_engine._new_client = instrumented
    account_id = None
    try:
        async def run():
            nonlocal account_id
            client = await tg.connection_engine.get_client()
            me = await client.get_me(input_peer=False)
            probe.require(me is not None, 'not_authenticated')
            account_id = me.id
            login = json.loads((ROOT / 'login-status.json').read_text())
            probe.require(login.get('phase') == 'SUCCESS' and
                          login.get('verified_account_id') == str(account_id), 'wrong_selected_account')
            report['account_id'] = str(account_id)
            # Explicit user confirmation: no other scrapers or existing budget.
            # Create only the missing account policy; never replace an existing one.
            with budget._transaction() as db:
                exists = db.execute('SELECT 1 FROM tgdata_budget_accounts WHERE account_id=?', (account_id,)).fetchone()
            if exists is None:
                budget.configure(account_id, daily_limit=CAP)
            before = budget.status(account_id)
            probe.require(before.limit <= CAP, 'unexpected_existing_budget_cap')
            report['budget_used_before'] = before.used
            resolved = await client(functions.contacts.ResolveUsernameRequest(USERNAME), flood_sleep_threshold=0)
            probe.require(isinstance(resolved.peer, (types.PeerChannel, types.PeerChat)), 'target_is_not_group')
            chat_id = utils.get_peer_id(resolved.peer)
            entity = next((c for c in resolved.chats if utils.get_peer_id(c) == chat_id), None)
            probe.require(entity is not None, 'resolved_group_missing')
            guard.chat_id = chat_id
            peer = utils.get_input_peer(entity)
            report['chat_id'] = str(chat_id)
            report['peer_kind'] = type(entity).__name__
            report['access_context'] = 'selected authenticated account, selected username only'
            report['end_observed'] = False
            offset = 0
            seen = set()
            for page in range(1, 6):
                guard.turn = page
                response = await client(functions.messages.GetHistoryRequest(
                    peer=peer, offset_id=offset, offset_date=None, add_offset=0,
                    limit=100, max_id=0, min_id=0, hash=0), flood_sleep_threshold=0)
                messages = response.messages
                if not messages:
                    report['end_observed'] = True
                    break
                for message in messages:
                    probe.require(isinstance(message, (types.Message, types.MessageService)), 'oracle_unknown_message_shape')
                    probe.require(utils.get_peer_id(message.peer_id) == chat_id, 'oracle_wrong_group')
                    probe.require(message.id not in seen, 'oracle_duplicate_id')
                    seen.add(message.id)
                    report['messages'].append(dict(id=str(message.id), date=probe._encode_date(message.date),
                                                  media_kind=type(message.media).__name__ if message.media else None))
                new_offset = min(m.id for m in messages)
                probe.require(offset == 0 or new_offset < offset, 'oracle_did_not_advance')
                offset = new_offset
                if len(messages) < 100:
                    report['end_observed'] = True
                    break
                if page < 5:
                    await asyncio.sleep(5)
            report['qualification_completed'] = True
            report['oldest_id'] = str(offset)
            client.session.save()
        await asyncio.wait_for(run(), timeout=180)
    except Exception as error:
        report['error_type'] = type(error).__name__
        report['error_chain'] = []
        seen_errors = set()
        current = error
        while current is not None and id(current) not in seen_errors:
            seen_errors.add(id(current))
            report['error_chain'].append(dict(kind=type(current).__name__, frames=[
                dict(file=Path(f.filename).name, function=f.name, line=f.lineno)
                for f in traceback.extract_tb(current.__traceback__)]))
            current = current.__cause__ or current.__context__
        if isinstance(error, probe.ProbeStop):
            report['stop_code'] = str(error)
    finally:
        try:
            await asyncio.wait_for(tg.close(), 10)
        except Exception as error:
            report['cleanup_error_type'] = type(error).__name__
        if account_id is not None:
            try:
                report['budget_used_after'] = budget.status(account_id).used
            except Exception as error:
                report['budget_error_type'] = type(error).__name__
        report['rpc'] = guard.rpc
        report['requested_slots'] = guard.slots
        save(output, report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('messages', 'rpc', 'account_id')}, sort_keys=True))
    print('Recorded message ID/date rows:', len(report['messages']))
    return 0 if report.get('qualification_completed') and not any(k.endswith('error_type') for k in report) else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    probe.require(not args.output.exists(), 'output_already_exists')
    os.chdir(CONFIG.parent)  # Preserve the selected existing relative session path.
    logging.disable(logging.CRITICAL)
    sys.exit(asyncio.run(capture(args.output)))
