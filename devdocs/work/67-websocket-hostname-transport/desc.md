> Session warmed at `240a208` (2026-11-26) — /arch-small-summary + /arch-intro.

# #67 — Connect to Telegram over its WebSocket transport by hostname

**The design this description rests on was decided by the traverse,** in `traverse/finding.md` on this branch (`e27b9c4`), against Telethon 1.45.0. This document says what the feature must achieve and how we will know it does. The plan decides how.

**Where this description sharpens or departs from the issue's wording:**
- **"Never resolve the name locally" (requirement 2)** holds whenever a proxy is configured: the proxy resolves the name.
  - With **no** proxy, `transport = websocket` is still allowed and connects **directly by name**, so the operating system resolves it. That is useful on networks that block Telegram's IP ranges but allow its web domain.
  - `require_proxy = true` keeps its meaning, and forbids the direct case for anyone who needs that.
- **"An unknown DC is an error" (requirement 4)** also covers Telethon's CDN download path, by construction: Telethon builds the CDN connection with the same connection class. Telethon 1.45.0 never requests CDN downloads anyway.
- **"Every DC by name" (requirement 4) means the five planet names,** `pluto`, `venus`, `aurora`, `vesta`, `flora` (`.web.telegram.org`) for DC 1–5.
  - The `kws1`–`kws5` names worked equally well in the probe, so the probe alone does not decide between the two families.
  - The planet names are chosen because an independent open-source client uses the same map (gotd/td, `telegram/dcs/prod.go`, commit `b4bf604`: `Domains: map[int]string{1: "wss://pluto.web.telegram.org/apiws", … 5: "wss://flora.web.telegram.org/apiws"}`), and because they read clearly in logs.
  - The media names (`<name>-1`) are not used.
- **"The default stays exactly as today" (requirement 1)** is made precise. With no `transport` key, or `transport = tcp`, three things are identical to today's:
  - the arguments tgdata passes to Telethon's `TelegramClient`;
  - the route log line;
  - the stepwise login's checkpoint fingerprint.

## Problem Statement

Some proxies send a connection out from their assigned exit address only when the target is given as a **hostname**. Given an IP address, they send it out from the proxy gateway's own shared addresses instead, or refuse it.

Every connection Telethon 1.45.0 opens goes to a data centre's **IP address**, and so does every connection tgdata opens, because tgdata builds all its clients through Telethon. With such a proxy, `proxy` / `require_proxy` keep every connection on the proxy, but they cannot change *what the proxy is asked to reach*. The account's Telegram traffic therefore cannot leave from its assigned address.

Telegram runs a second way in: its WebSocket transport, reached by hostname at `wss://<name>.web.telegram.org/apiws`. A probe on 2026-11-26 used no account, no session and no api_id. It went through such a proxy by HTTP CONNECT, with IP targets refused, and showed:
- **Every DC worked.** For DC 1–5, TLS verified, the WebSocket handshake answered (`101`, `protocol=binary`), an MTProto auth key was created over Telethon's own obfuscated transport, and a ping was answered. All of it left from the proxy's assigned address.
- **Idle connections are cut eventually.** One survived 150 s idle and was cut by 300 s.

tgdata has no way to use that transport today.

## User Value Proposition

An operator adds one line to an account's `[Telegram]` section, `transport = websocket`. From then on, every connection that account's clients open reaches Telegram **by name**, and never by IP:
- login;
- reads and downloads, including from other DCs;
- verified account operations;
- the account pool;
- the worker;
- every reconnect.

With a hostname-routing proxy, all of that traffic leaves from the account's assigned address.

**Nothing else changes for them:**
- the same session files, device identity, proxy settings and public API;
- accounts that do not opt in behave exactly as before;
- a pool can mix TCP and WebSocket accounts in one process.

**If the transport cannot work, it fails loudly instead of quietly falling back to an IP:**
- a configuration problem — an unknown `transport` value, a DC with no known hostname, a certificate that does not verify — stops at once, with a message naming the transport and the host;
- a network problem is retried like any other connection error.

The operator can confirm the transport is active three ways:
- the one-time route log line;
- `health_check()`;
- Telethon's own `Connecting to <host>:443/…` line for each connection.

## Success Criteria

**Behaviour:**
1. **The key is read and checked.** `transport` in an account's `[Telegram]` section accepts `tcp` (the default, and what an absent key means) and `websocket`, case-insensitively. Any other value raises a configuration error (a `ValueError`) before any connection is attempted.
2. **One switch covers every client.** With `transport = websocket`, every client built by tgdata's client factory (`ConnectionEngine._new_client`) uses the WebSocket transport. That covers the persistent client, `ephemeral_client()`, the verified account operations, `LoginFlow`, `AccountPool`'s sources and the `Worker`. No consumer's code changes.
3. **Never an IP.** Proven offline with a recording proxy (HTTP CONNECT and SOCKS5), whose every destination is one of the five hostnames on port 443 and never an IP literal, on each of these paths:
   - main connect;
   - reconnect;
   - a connection to another DC;
   - the strict-option paths (account operations, the pool, the stepwise login);
   - a pool that mixes a `tcp` account and a `websocket` account, where each reaches only its own kind of destination.
4. **No IP is ever held or accepted.**
   - A connection object built for DC 2 holds `venus.web.telegram.org`, with no IP anywhere in it.
   - The function that opens the WebSocket refuses an IP-literal host.
   - An unmapped DC number raises at once.
5. **Failures are classified correctly.** Tested through Telethon's real connect-retry loop and `AccountPool._failure`.
   - **Stop immediately, never retried** (a `ValueError`-family error): an unknown value, an unmapped DC, a certificate failure, an IP-literal host.
   - **Retried as `transport`** (a `ConnectionError`): a handshake that does not return `101`, a reset, a WebSocket protocol violation, a server close.
   - **Mid-session closes** are logged by Telethon as a warning, without a traceback.
   - **No error message contains a credential.**
6. **No health noise.** No error the transport raises produces an account-health verdict (`health.classify(...)` returns `None`).
7. **The login checkpoint stays correct.**
   - The stepwise login's checkpoint binding includes `transport` **only** when it is not `tcp`, so every existing TCP checkpoint restores exactly as before.
   - Changing the transport between `start` and `submit` invalidates the checkpoint, as changing the proxy does.
8. **The default path is unchanged.** For `tcp` or no key, the following equal values captured **before** any code changes:
   - the `TelegramClient` constructor arguments;
   - the route log text;
   - the checkpoint fingerprint.

   The transport's module is not imported at all unless an account selects it.
9. **Observability.**
   - The one-time route log line says the connections go "over WebSocket by name" for `websocket` accounts only.
   - `health_check()` reports the transport, beside its existing `proxy` field.

**Guards against drift:**

10. **A version canary.** In the style of the existing "run after any Telethon upgrade" test, it asserts each Telethon internal the transport relies on:
    - the connection constructor's arguments;
    - the connect method's arguments;
    - the proxy code dialling the stored host and turning the proxy library's errors into `ConnectionError`;
    - the obfuscation layer taking its reader and writer when the header is written;
    - Telethon's four connection-construction sites passing the DC number;
    - CDN downloads never being requested.
11. **No new runtime dependency.** The WebSocket code uses only Python's standard library, and `setup.py`'s extras are unchanged.

**Documentation:**

12. **What becomes false is corrected in the same change:**
    - the comment in `connection_engine.py` that calls remote DNS "moot";
    - the docstrings of `parse_proxy_url` and `_new_client`;
    - `docs/stepwise_login.md`'s list of binding fields.
13. **The README gains a section, "Connecting through Telegram's WebSocket door",** covering:
    - the key;
    - what the proxy must allow (a tunnel to `*.web.telegram.org:443`);
    - "never an IP, no fallback";
    - the no-proxy case;
    - what each kind of failure looks like;
    - how to confirm the transport is active;
    - the verified Telethon version;
    - the risks below.

    New text says "network transport", so it is not confused with the "transport envelopes" the README already describes.

**Live — gated on the maintainer's explicit go, after criteria 1–13 pass offline:**

14. **The real account over `transport = websocket`:**
    - logs in, reads, and downloads from another DC;
    - reuses an existing session file made over TCP;
    - stays connected through more than 300 s idle;
    - every exit leaves from the proxy's assigned address, and none by IP.

    Any Telegram error that appears only under WebSocket is recorded.

**Settled by observation:**
- **The `Origin` header is not required, and the transport does not send one.**
  - **The run:** a no-account probe with `--no-origin`, 2026-11-26 13:32 UTC, through the same kind of proxy.
  - **The result:** DC 1–5 (pluto, venus, aurora, vesta, flora) each completed TLS (certificate `*.web.telegram.org`), the WebSocket `101` with `protocol=binary`, an auth key and a ping — every connection from the proxy's assigned address.
  - **Why drop it rather than keep it:** tgdata presents a desktop-app identity when it connects (the pinned device identity), and a browser `Origin` would contradict that rather than blend in. It is also one constant fewer.
  - **Re-confirmation:** the live run (criterion 14) uses this configuration, so it re-confirms the result with the real account.

**Still open — decided by observation, not by this description:**
- **The live calibration** (criterion 14). The name map and the plain obfuscation header are calibrated on one day's no-account probe. If the real account disagrees, the fix is local to the transport's connection class. Criterion 14 is where that would show.

## Scope Boundaries

**This feature will not:**
- **Support MTProto proxies** (`tg://proxy`, `t.me/proxy`). `parse_proxy_url` keeps refusing them.
- **Fall back.** Never to TCP, and never to an IP — not at connect, on reconnect, on a DC switch, or at login.
- **Change the default path** in any observable way (criterion 8).
- **Make the hostnames configurable.** No per-account host override, and no switching between the planet and `kwsN` families on reconnect. A renamed endpoint is answered by a release.
- **Add a dependency.** No WebSocket library, and no new extra.
- **Pin Telethon at runtime for this transport.** The canary (criterion 10) guards the internals. The exact pins that `AccountPool` and `Worker` already have stay as they are.
- **Send transport-level pings.** Telethon's 60 s keep-alive runs on every connected client, strict ones included. Connections to other DCs are closed by Telethon after 60–120 s idle, inside the 150–300 s idle cut.
- **Change session files, device identity, the request-level guards** (read budget, join admission, heartbeat, health evidence, per-request flood threshold), **`AccountPool._failure` or `health.classify`.**
- **Imitate the web clients.** The handshake sends no `Origin` header, and there is no change to the wire codec or to the identity fields Telethon sends at login.
- **Support Telethon 2.x,** or any Telethon other than the 1.45.0 baseline it is verified on.
- **File or draft anything upstream** with Telethon.

**Risks accepted, and documented in the README** (none is removable in code):
- **The endpoint is unpublished.** Telegram documents DC IP addresses, not these hostnames, and could change them. A renamed endpoint looks exactly like an outage: every attempt fails at the proxy's name lookup, and the pool keeps cooling down and retrying.
- **How Telegram treats the account is unknown** — one whose earlier sessions came from a desktop client, now arriving through the web transport.
- **The web relays may have rate limits of their own.** Unverified.
- **A login key made over TCP should keep working over WebSocket,** because keys belong to a DC, not a transport. Only the live run (criterion 14) shows it.
- **Servers need a working certificate store.** Without one, every WebSocket connection stops at once, with a certificate error.
- **A policy refusal could look like an account problem.** If Telegram ever refuses the web transport by policy as a Telegram error on the first request, and its code is one `health.classify` reports as `unclassified`, it would read as an account problem. Operators should compare against `transport = tcp` before treating such an event as an account verdict.

## Priority Level

**High — P1, confirmed.**
- **It blocks the use it exists for.** Without it, a hostname-routing proxy cannot carry an account's Telegram connections from its assigned address, and tgdata offers no workaround.
- **It is opt-in and contained.** The traverse found it needs one connection class plus small edits to the config reader, the client factory and the login binding, with no consumer changes and the default path byte-identical. That keeps the cost of shipping it low.
- **It is not P0.** Accounts that do not use such a proxy are unaffected.
