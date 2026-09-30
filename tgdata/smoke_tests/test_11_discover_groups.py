"""
Smoke test for group discovery: search_groups, similar_groups, linked_groups,
discover_groups, and the build_search_queries helper.

Cost, stated up front: about a dozen requests and THREE username resolutions
(the request Telegram punishes hardest) from the configured account. Do not
scale the limits up. Reconnect-and-retry (a dropped connection) cannot be
exercised without cutting the network; it is covered by reading.
"""
# To run: python -m tgdata.smoke_tests.test_11_discover_groups [config.ini]

import asyncio
import logging
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd

from tgdata import TgData, DiscoveryInterrupted, build_search_queries
from tgdata.discovery_engine import COLUMNS, DiscoveryEngine

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "config.ini"


class _Warnings(logging.Handler):
    """Collects WARNING records from the discovery engine."""
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


WARNINGS = _Warnings()
logging.getLogger("tgdata.discovery_engine").addHandler(WARNINGS)
logging.getLogger("tgdata.discovery_engine").setLevel(logging.INFO)


# ------------------------------------------------------------ no network --

async def test_query_builder():
    print("TEST: build_search_queries (no network)...")
    try:
        qs = build_search_queries(["Анталия", "Antalya"], topics=["чат", "аренда"], prefixes=["Турция"])
        assert len(qs) == 12, len(qs)
        assert qs[0] == "Анталия"
        assert "Анталия аренда" in qs and "аренда Анталия" in qs
        assert len({q.lower() for q in qs}) == len(qs)
        assert len(build_search_queries(["Анталия", "Antalya"], topics=["чат", "аренда"],
                                        prefixes=["Турция"], both_orders=False)) == 8
        assert build_search_queries(["a", " a ", "", "A"]) == ["a"]
        print(f"✓ 12 queries in both orders, 8 in one; case-insensitive dedup")
        return True
    except Exception as e:
        print(f"✗ Query builder test failed: {e}")
        return False


async def test_empty_frame():
    print("\nTEST: empty and unresolved frames (no network)...")
    try:
        df = DiscoveryEngine._frame([])
        assert list(df.columns) == COLUMNS and len(df) == 0
        assert str(df['GroupID'].dtype) == 'Int64' and str(df['IsChannel'].dtype) == 'boolean'
        print("✓ Empty result keeps every column and its dtypes")

        df = DiscoveryEngine._frame([DiscoveryEngine._unresolved_row("abcde", "id:1")])
        assert pd.isna(df.loc[0, 'GroupID']) and pd.isna(df.loc[0, 'IsChannel'])
        assert df.loc[0, 'Username'] == "@abcde" and df.loc[0, 'Identifier'] == "@abcde"
        assert df.loc[0, 'FoundVia'] == 'link' and str(df['GroupID'].dtype) == 'Int64'
        print("✓ Unresolved link row: NA id and flags, @name kept, dtypes unchanged")

        from tgdata.discovery_engine import TME_LINK, RESERVED_PATHS
        text = ("see https://t.me/antalyadaa/123 and t.me/s/alanya_news, t.me/boost/first_turkiye, "
                "not t.me/+AbCdEf, not t.me/c/1234/5, not t.me/joinchat/xyz, telegram.me/life_mersin")
        names = [n for n in TME_LINK.findall(text) if n.lower() not in RESERVED_PATHS]
        assert names == ["antalyadaa", "alanya_news", "first_turkiye", "life_mersin"], names
        print("✓ Link regex: deep links, s/, boost/ and telegram.me kept; invites, c/ and joinchat skipped")
        return True
    except Exception as e:
        print(f"✗ Frame test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# --------------------------------------------------------------- live --

def _check_shape(df, via_expected=None):
    assert list(df.columns) == COLUMNS, list(df.columns)
    if via_expected is not None and not df.empty:
        assert set(df['FoundVia']) <= via_expected, set(df['FoundVia'])
    ids = df['GroupID'].dropna()
    assert ids.is_unique, "duplicate GroupID"


async def pick_seed(tg):
    groups = await tg.list_groups()
    if groups.empty:
        return None, None
    channels = groups[groups['IsChannel'] & ~groups['IsMegagroup'].astype(bool) & groups['Username'].notna()]
    if channels.empty:
        channels = groups[groups['IsChannel'] & groups['Username'].notna()]
    if channels.empty:
        return None, groups
    row = channels.iloc[0]
    return {'id': int(row['GroupID']), 'username': row['Username'], 'title': row['Title']}, groups


async def test_live():
    print("\nTEST: live discovery (about a dozen requests, three username resolutions)...")
    tg = TgData(CONFIG)
    ok = True
    try:
        seed, groups = await pick_seed(tg)
        if seed is None:
            print("✗ No channel with a @username among the account's dialogs — follow one and rerun")
            return False
        print(f"Seed: {seed['username']} ({seed['title']!r}), {len(groups)} dialogs")

        # search_groups
        df = await tg.search_groups("Анталия", limit=20, pace=1.0)
        _check_shape(df, {'search'})
        assert df.empty or (df['FoundBy'] == "Анталия").all()
        print(f"✓ search_groups('Анталия'): {len(df)} rooms")
        print(df[['Identifier', 'Title', 'IsChannel', 'IsMegagroup', 'ParticipantsCount']].head(5).to_string())
        empty = await tg.search_groups("zzqqxx_no_such_room_123", limit=5, pace=1.0)
        _check_shape(empty)
        assert empty.empty, len(empty)
        print("✓ A nonsense query returns zero rows with every column")

        # similar_groups
        sim = await tg.similar_groups(seed['username'], rounds=1, pace=1.0)
        _check_shape(sim, {'similar'})
        assert seed['id'] not in set(sim['GroupID'].dropna().astype(int)), "the seed came back as a find"
        print(f"✓ similar_groups({seed['username']}, rounds=1): {len(sim)} rooms (0 is legitimate on a non-Premium account)")

        # linked_groups, unresolved then resolved with a budget of 3
        links = await tg.linked_groups(seed['username'], posts=50, resolve=False, pace=1.0)
        _check_shape(links, {'link'})
        assert links['GroupID'].isna().all() and links['Username'].notna().all()
        assert str(links['GroupID'].dtype) == 'Int64'
        print(f"✓ linked_groups(resolve=False): {len(links)} linked names, ids NA, dtype kept")
        before = len(WARNINGS.messages)
        resolved = await tg.linked_groups(seed['username'], posts=50, resolve=True, max_resolve=3, pace=1.0)
        _check_shape(resolved, {'link'})
        got_ids = int(resolved['GroupID'].notna().sum())
        assert got_ids <= 3, got_ids
        if len(links) > 3:
            assert any("username bound" in m for m in WARNINGS.messages[before:]), "no cap warning logged"
            print(f"✓ linked_groups(resolve=True, max_resolve=3): {got_ids} resolved, cap warning logged")
        else:
            print(f"✓ linked_groups(resolve=True, max_resolve=3): {got_ids} resolved of {len(links)}")

        # discover_groups with the callback and heartbeat, link_sources=2, no resolution
        received, phases = [], []
        before = len(WARNINGS.messages)
        disc = await tg.discover_groups(
            seeds=[seed['username']], queries=["Анталия чат"], similar_rounds=1,
            mine_links=True, link_sources=2, resolve_links=False, pace=1.0,
            heartbeat=phases.append, found_callback=received.append)
        _check_shape(disc, {'similar', 'search', 'link'})
        assert len(received) == len(disc), (len(received), len(disc))
        assert [r['Identifier'] for r in received] == list(disc['Identifier'])
        assert {"search", "similar", "pause"} <= set(phases), set(phases)
        found_before_links = int((disc['FoundVia'] != 'link').sum())
        if found_before_links > 2:
            assert any("Mining links from the first 2" in m for m in WARNINGS.messages[before:]), "no source-cap warning"
        print(f"✓ discover_groups: {len(disc)} rooms; {len(received)} callback rows in order; "
              f"phases seen: {sorted(set(p.split()[0] for p in phases))}")

        # round-trip: a discovered room is usable by bare id
        first = disc[disc['GroupID'].notna()]
        if first.empty:
            print("! nothing with an id discovered — round-trip skipped")
        else:
            gid = int(first.iloc[0]['GroupID'])
            msgs = await tg.get_messages(group_id=gid, limit=3)
            print(f"✓ get_messages({gid}) on a discovered room: {len(msgs)} messages, no GroupAccessError")
    except DiscoveryInterrupted as e:
        print(f"✗ Interrupted: {e} — {len(e.found)} rooms kept in .found; retry after {e.retry_after}s")
        ok = False
    except Exception as e:
        print(f"✗ Live test failed: {e}")
        import traceback
        traceback.print_exc()
        ok = False
    finally:
        await tg.close()
    return ok


async def main():
    print("Group Discovery Tests")
    print("=" * 60)
    print(f"config: {CONFIG}")
    print("Cost: ~12 requests + 3 username resolutions on the live account. Do not scale up.\n")

    tests = [test_query_builder, test_empty_frame, test_live]
    results = []
    for test in tests:
        try:
            results.append(await test())
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\nSummary")
    print("=" * 60)
    passed, total = sum(results), len(results)
    print(f"Passed: {passed}/{total}")
    if WARNINGS.messages:
        print("Engine warnings during the run:")
        for m in WARNINGS.messages:
            print(f"  - {m}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
