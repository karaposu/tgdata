"""Probe for scoped/10 — the REORDER experiment named in critic.md.

About five READ-ONLY requests from the configured account, through tgdata's
own persistent session (the real composition), to settle the premises the
plan builds on BEFORE the discovery engine is written:

  [0] authorization check through the non-interactive ephemeral client
        -> never reaches Telethon's login prompt in an unattended shell
  [1] recommendations for a broadcast channel the account follows
        -> does channels.GetChannelRecommendationsRequest yield anything on
           THIS account (the finder's numbers came from a Premium account)?
  [2] global search: the seed's own title, plus any extra terms given
        -> does contacts.SearchRequest return chats for a name query?
  [3] what the returned objects carry
        -> type, min flag, access hash present?, participants_count
           (the plan's parity promise depends on the last one)
  [4] get_messages(limit=1) by BARE id on a returned room the account is
      NOT a member of, through the normal fetch path
        -> is a discovered room usable by id with no dialog sync?
           (P1 in critic.md — the premise that would REWRITE the plan)

Nothing is joined, sent or written to Telegram. Run from the repo root:

    .venv/bin/python devdocs/scoped/10/probe_discovery.py [config.ini] [extra search term ...]

Disqualifying: [2] returns zero chats for an existing title, or [4] fails.
Passing:       [2] >= 1 chat and [4] returns a row with no "syncing dialogs"
               line in the log above it. An EMPTY [1] with no error is a
               documentation downgrade, not a failure.

One live client per session file: this probe opens its clients briefly and
closes every one of them; run it beside a standing loop only from the same
machine, and never leave it running.
"""

import asyncio
import logging
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, REPO)   # the tgdata SOURCE in this repo (0.0.7), whatever the venv has installed

from telethon import functions                      # noqa: E402
from telethon.errors import FloodWaitError          # noqa: E402
from telethon.tl import types as tl                 # noqa: E402

from tgdata import TgData, GroupAccessError         # noqa: E402
from tgdata.connection_engine import AuthRequiredError  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

PACE_S = 2.0
CONFIG = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(REPO, "config.ini")
EXTRA_QUERIES = sys.argv[2:]


def describe(c) -> str:
    return (f"{type(c).__name__} id={getattr(c, 'id', None)} "
            f"title={getattr(c, 'title', None)!r} username={getattr(c, 'username', None)} "
            f"min={getattr(c, 'min', None)} "
            f"access_hash={'yes' if getattr(c, 'access_hash', None) else 'NO'} "
            f"participants_count={getattr(c, 'participants_count', None)} "
            f"broadcast={getattr(c, 'broadcast', None)} megagroup={getattr(c, 'megagroup', None)}")


async def main() -> int:
    print(f"config: {CONFIG}")
    tg = TgData(CONFIG)
    cfg = tg.connection_engine._load_config()
    print(f"session: {cfg.session_file}.session  exists={os.path.exists(cfg.session_file + '.session')}")

    # [0] authorization check that can never prompt: the use-and-close client
    try:
        async with tg.connection_engine.ephemeral_client() as probe:
            me = await probe.get_me()
            print(f"[0] authorized as id={me.id} username={me.username} premium={getattr(me, 'premium', None)}")
    except AuthRequiredError as e:
        print(f"[0] NOT authorized: {e}")
        return 2

    try:
        groups = await tg.list_groups()
        if groups.empty:
            print("no dialogs at all — cannot pick a seed; join or follow one public channel and rerun")
            return 2
        mine = {int(x) for x in groups["GroupID"]}
        broadcast = groups[groups["IsChannel"] & ~groups["IsMegagroup"].astype(bool) & groups["Username"].notna()]
        seeds = broadcast if not broadcast.empty else groups[groups["IsChannel"] & groups["Username"].notna()]
        if seeds.empty:
            print("no channel with a @username among the account's dialogs — follow one public channel and rerun")
            return 2
        print(f"dialogs: {len(groups)} groups/channels, {len(broadcast)} broadcast channels with a username")

        found = []
        async with tg.connection_engine.session() as client:
            # [1] recommendations — up to three seeds, stop at the first non-empty answer
            for _, s in seeds.head(3).iterrows():
                ent = await client.get_input_entity(int(s["GroupID"]))   # a dialog: cached, no lookup
                r = await client(functions.channels.GetChannelRecommendationsRequest(channel=ent),
                                 flood_sleep_threshold=0)
                print(f"\n[1] recommendations for {s['Username']} ({s['Title']!r}): "
                      f"{len(r.chats)} chats in a {type(r).__name__}")
                for c in r.chats[:5]:
                    print("     ", describe(c))
                found += list(r.chats)
                await asyncio.sleep(PACE_S)
                if r.chats:
                    break

            # [2] global search: the first seed's own title (known to exist), then any extra terms
            for q in [str(seeds.iloc[0]["Title"])[:32]] + EXTRA_QUERIES:
                r = await client(functions.contacts.SearchRequest(q=q, limit=20), flood_sleep_threshold=0)
                print(f"\n[2] search {q!r}: {len(r.chats)} chats, {len(r.users)} users")
                for c in r.chats[:8]:
                    print("     ", describe(c))
                found += list(r.chats)
                await asyncio.sleep(PACE_S)

        # [3] summary of what the objects carry
        chans = [c for c in found if isinstance(c, (tl.Channel, tl.Chat))]
        print(f"\n[3] {len(found)} objects returned: "
              f"{sum(isinstance(c, tl.Channel) for c in found)} Channel, "
              f"{sum(isinstance(c, tl.Chat) for c in found)} Chat, "
              f"{sum(isinstance(c, (tl.ChannelForbidden, tl.ChatForbidden)) for c in found)} Forbidden; "
              f"min={sum(bool(getattr(c, 'min', False)) for c in chans)}; "
              f"with participants_count={sum(getattr(c, 'participants_count', None) is not None for c in chans)}")

        # [4] a returned room the account is NOT in, fetched by bare id through the fetch path
        outsider = next((c for c in found
                         if isinstance(c, tl.Channel) and c.id not in mine and not getattr(c, "min", False)),
                        None)
        if outsider is None:
            print("\n[4] every returned room is one the account already follows — the cache premise "
                  "could not be tested. Pass a search term for a public room you are NOT in and rerun.")
            return 3
        print(f"\n[4] fetching 1 message by BARE id from a non-member room: {describe(outsider)}")
        print("     (watch the log: a 'syncing dialogs' line here means the cache premise is FALSE)")
        try:
            df = await tg.get_messages(group_id=outsider.id, limit=1)
            print(f"     OK — {len(df)} row(s) returned by id alone")
            return 0
        except GroupAccessError as e:
            print(f"     FAIL — GroupAccessError: {e}\n     -> discovered rows need an access hash or a retained entity; re-plan")
            return 1
    except FloodWaitError as e:
        print(f"\nTelegram asks for a {e.seconds}s wait on {e.request.__class__.__name__} — rerun after it")
        return 4
    finally:
        await tg.close()


if __name__ == "__main__":
    import signal
    signal.alarm(180)          # hard stop: a probe that hangs (a prompt, a lock) must die, not wait
    sys.exit(asyncio.run(main()))
