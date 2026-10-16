# Revision3 planning evidence

Purpose: resolve whether #50's existing LoginFlow can retain source ownership when
SIGINT is handled as a cancellation request rather than injected KeyboardInterrupt.
This is a small phase-local driver experiment. It is **not** the proposed complete
command owner, a product patch, or the mandatory combined prebuild.

Run with Python3.11.10 / Telethon1.45.0:

```text
python devdocs/work/50-terminal-account-login/replan-r3/interrupt_probe.py
```

Executed in a bounded subprocess (15s maximum), no sockets, no real credentials.
Six cases PASS: signal inside phone validation; signal while actual SRP computation
is active; repeated signals during native cleanup; repeated signals during an
awaited source request; an already-done future carrying KeyboardInterrupt; and
uncancellable retirement with repeated signals. Actual LoginFlow and SDK cleanup
are used with fixture41's controlled source. Every observed wire closed; no pending
loop task remained. No product file was modified.

The SRP case recorded one password request and ended uncertain after cancellation.
This is important: cancellation is cooperative, so an already-started action may
have remote effects before it observes the stop. The new command must forbid NEW
login actions after a stop, preserve known/uncertain source state and refuse further
publication; it must not promise that a stop prevents every in-flight RPC.

The probe's signal handler schedules at most one cancellation through the loop;
its retirement mode only records stop. It does not prove command-wide sticky stop,
phase transitions, actual prompt terminal restoration, reporting/finalization or
publication integration. Those are explicit full-prebuild obligations in revision3.
The earlier failed real-PTY/SRP evidence in ../pr-probes/ is unchanged.

Ground truth inspected: the installed Python3.11.10 run_until_complete and its
completion callback; actual getpass.unix_getpass; LoginFlow action/cleanup ownership;
CONTRIBUTING §7.4/§7.5. Relevant primary documentation:

- [Python signal exceptions](https://docs.python.org/3.11/library/signal.html#note-on-signal-handlers-and-exceptions)
  explains why raising from a signal handler can interrupt arbitrary bytecode.
- [Python3.11 scheduling](https://docs.python.org/3.11/library/asyncio-eventloop.html#asyncio.loop.call_soon_threadsafe)
  defines thread-safe callback scheduling and closed-loop refusal.
- [Current Python scheduling](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.call_soon_threadsafe)
  explicitly documents signal-handler/reentrant use. This is corroboration, not
  a claim that the locally executed Python is that documentation's newer version.

Native Python3.7 and live Telegram remain unqualified. No physical crash or stalled
filesystem/disconnect timeout guarantee is inferred. The probe supports the local
choice; only the complete revised candidate can satisfy the next implementation gate.
