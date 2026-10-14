"""Caller-owned original storage and bounded provisional photo-trail views.

Offline demo: python examples/photo_trails.py --demo
The existing AlbumReceiver owns original acceptance. This optional view performs
no writes and never creates a source receipt or retains downloaded media bytes.
"""

import argparse
import asyncio
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tgdata import MessageBatch, SQLiteSyncStore, PhotoTrailPolicy, PhotoTrailError, fold_photo_trails
from tgdata.photo_trails import _limits, _policy
from tgdata.message_batch import MIN_LONG, MAX_MESSAGE_ID
from tgdata.sync_engine import SyncEngine
from examples.album_assembly import AlbumReceiver, ReceiverError


def load_photo_trails(receiver, chat_id, *, after_id, through_id, policy=None):
    """Read one closed current stored interval, then compute its optional view.

    Every known member of a selected post must lie in (after_id, through_id].
    A split album refuses rather than silently widening/clipping context. Use
    this receiver's chosen member/byte policy; inference is disabled by default.
    Original acceptance and source acknowledgment are separate operations.
    """
    if not isinstance(receiver, AlbumReceiver):
        raise PhotoTrailError('receiver must be an AlbumReceiver')
    _limits(receiver.max_members, receiver.max_bytes)
    policy = _policy(policy)
    if type(chat_id) is not int or not MIN_LONG <= chat_id <= -1:
        raise PhotoTrailError('chat_id must be a canonical negative integer')
    if (type(after_id) is not int or type(through_id) is not int
            or not 0 <= after_id <= through_id <= MAX_MESSAGE_ID):
        raise PhotoTrailError('interval requires 0 <= after_id <= through_id <= MAX_MESSAGE_ID')
    with receiver._open() as db:
        db.execute('BEGIN')
        receiver._validate(db)
        arguments = (receiver.collection, chat_id, after_id, through_id)
        where = ('WHERE collection COLLATE BINARY=? AND chat_id=? '
                 'AND message_id>? AND message_id<=?')
        count, key_bytes, invalid = db.execute(
            'SELECT COUNT(*),COALESCE(SUM(length(CAST(post_id AS BLOB))),0),'
            "COALESCE(SUM(typeof(post_id)!='text' OR typeof(chat_id)!='integer' "
            "OR typeof(message_id)!='integer'),0) FROM album_members " + where, arguments).fetchone()
        if invalid:
            raise ReceiverError('selected member keys have invalid types')
        if count > receiver.max_members or key_bytes > receiver.max_bytes:
            raise PhotoTrailError('selected context exceeds member or key-byte limit')
        keys = [row[0] for row in db.execute(
            'SELECT DISTINCT post_id COLLATE BINARY FROM album_members ' + where +
            ' ORDER BY post_id COLLATE BINARY', arguments)]
        stats, total_count, total_bytes = {}, 0, 0
        for key in keys:
            stats[key] = receiver._stats(db, key)
            if not stats[key][0]:
                raise ReceiverError('selected original post is missing')
            first, last, wrong_chat = db.execute(
                'SELECT MIN(message_id),MAX(message_id),COALESCE(SUM(chat_id!=?),0) '
                'FROM album_members WHERE collection COLLATE BINARY=? AND post_id COLLATE BINARY=?',
                (chat_id, receiver.collection, key)).fetchone()
            if wrong_chat:
                raise ReceiverError('selected original post has inconsistent chat identity')
            if first <= after_id or last > through_id:
                raise PhotoTrailError('interval splits a known stored post; choose a wider explicit interval')
            total_count += stats[key][0]
            total_bytes += stats[key][1]
            if total_count > receiver.max_members or total_bytes > receiver.max_bytes:
                raise PhotoTrailError('selected originals exceed member or byte limit')
        if total_count != count:
            raise ReceiverError('selected rows do not match the closed original-post scope')
        posts, used = [], 0
        for key in keys:
            post = receiver._load(db, key, stats=stats[key], max_bytes=receiver.max_bytes-used)
            if post is None:
                raise ReceiverError('selected original post is missing')
            used += len(post.to_json().encode('utf-8'))
            posts.append(post)
    # Values are immutable and already belong to one snapshot. Release the read
    # lock before computing a view; no current database lookup is needed here.
    return fold_photo_trails(posts, policy=policy, max_members=receiver.max_members,
                             max_bytes=receiver.max_bytes)


def _demo_batch(after_id, limit):
    records = []
    for ident in [i for i in (1, 2, 3, 4) if i > after_id][:limit]:
        records.append(dict(id=str(ident), kind='message', date='2026-10-15T00:00:0{}.000000Z'.format(ident),
                            edit_date=None, text={1:'An original text', 2:'', 3:'', 4:'A later album caption'}[ident],
                            sender=dict(id='88', name=None, username=None), post_author=None,
                            reply_to_id=None, forward_from_id=None, grouped_id=None if ident == 1 else '7',
                            service_action=None, media=None if ident == 1 else dict(
                                kind='photo', id=str(ident), mime_type='image/jpeg', file_name=None,
                                size=None, downloadable=False, blob=None)))
    reason = 'end' if not records or records[-1]['id'] == '4' else 'limit'
    return MessageBatch._from_records(-1000000000007, after_id, records, 'references', reason)


def _member_groups(view):
    originals = {post.post_id: post for post in view.posts}
    return tuple(tuple(sorted(ident for key in group for ident in originals[key].member_ids))
                 for group in view.groups)


async def demo(directory):
    chat = -1000000000007
    destination = AlbumReceiver(directory/'originals.sqlite3', 'demo', create=True)
    progress = SQLiteSyncStore(directory/'progress.sqlite3')
    calls = []
    async def read(chat_id, **options):
        calls.append(options)
        return _demo_batch(options['after_id'], options['limit'])
    source = SyncEngine(read, progress)
    await source.initialize(chat, after_id=0)
    first = await source.prepare(chat, limit=1)
    destination.accept(first)
    source = SyncEngine(read, SQLiteSyncStore(progress.path, create=False))
    destination = AlbumReceiver(destination.path, 'demo')
    replay = await source.prepare(chat, limit=1)
    assert replay.to_json() == first.to_json() and len(calls) == 1
    destination.accept(replay)
    await source.acknowledge(chat, replay.batch_id)
    second = await source.prepare(chat, limit=2)
    destination.accept(second)
    await source.acknowledge(chat, second.batch_id)
    policy = PhotoTrailPolicy(enabled=True)
    old = load_photo_trails(destination, chat, after_id=0, through_id=3, policy=policy)
    assert _member_groups(old) == ((1, 2, 3),) and old.folded_photos == 2
    last = await source.prepare(chat, limit=1)
    destination.accept(last)
    await source.acknowledge(chat, last.batch_id)
    current = load_photo_trails(destination, chat, after_id=0, through_id=4, policy=policy)
    assert _member_groups(current) == ((1,), (2, 3, 4)) and _member_groups(old) == ((1, 2, 3),)
    assert (await source.status(chat)).after_id == 4 and len(calls) == 3
    print('Lost acknowledgment replayed without another source read.')
    print('Two photo messages were provisionally attached to the earlier text.')
    print('A later album caption withdrew that association; all four originals remain.')
    print('Source acknowledged through4; photo-trail views remain provisional.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', required=True)
    parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='tgdata_photo_trails_') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('demo forbids network')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('demo forbids network')):
        asyncio.run(demo(Path(tmp)))


if __name__ == '__main__':
    main()
