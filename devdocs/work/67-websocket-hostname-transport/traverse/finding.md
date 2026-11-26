---
status: active
model: claude-opus-5-5[1m]
effort: unknown
---
# Finding: the elegant design for tgdata's WebSocket transport (issue #67)

## Question

**What is the most elegant way to add `transport = websocket` to tgdata,** a Telegram data library built on Telethon 1.45.0?
- **The aim:** an account can connect to Telegram's WebSocket endpoint ("the door", `wss://<name>.web.telegram.org/apiws`) **by hostname**, through its configured proxy, and never by IP address.
- **The constraint:** this must not harm or break tgdata's existing design, which the maintainer considers elegant and wants kept that way.

The inquiry also had to surface concerns nobody had raised yet, and settle or route ten open design points.

**The goal:** a stable, decided design from which the feature's description (`desc.md`) and implementation plan (`plan.md`) can be written. It covers:
- decisions on the ten points;
- a register of concerns;
- a test strategy;
- the documentation that must change.

## Finding Summary

- **The transport is one Telethon connection class.** tgdata passes it to Telethon's constructor only when an account sets `transport = websocket`.
- **Almost everything else already exists and is reused unchanged:**
  - Telethon's routing of each data centre;
  - its proxy code;
  - its reconnect and keep-alive;
  - its retry rules;
  - tgdata's single client factory, its request-level guards, the account pool's failure classification, and session files.
- **"Never an IP" holds by construction, at two layers:**
  - the class hands Telethon the hostname in place of the IP it was given, so the object never holds an IP;
  - the function that opens the WebSocket refuses an IP address outright.
- **The change to existing code is four small edits:**
  - the config reader;
  - one branch in the client factory;
  - one conditional field in the login checkpoint's binding;
  - two observability additions.
- **No consumer changes.** `TgData`, the account pool, the worker and the stepwise login all inherit the transport through the one factory.
- **The default is byte-identical:** the same constructor arguments, log text and login-binding hash for every account that does not opt in.
- **Failures are classified by exception type, the only signal Telethon and the account pool read:**
  - configuration problems — an unknown value, an unknown data centre, a certificate that fails to verify — stop immediately;
  - network problems are retried.
- **Data centres map to fixed names:** DC 1–5 → `pluto`, `venus`, `aurora`, `vesta`, `flora` `.web.telegram.org`.
  - The original reason for choosing these names over the `kws1`–`kws5` family was wrong. Both families worked equally in the probe.
  - The choice stands on a different reason: an independent Telegram client library uses the same names.
- **No new dependencies, and no transport-level pings.** The WebSocket code is hand-written and Telethon-free. Telethon's existing 60-second keep-alive covers the relay's idle cut-off, which falls between 150 and 300 seconds.
- **The transport module is imported only when an account selects it,** so a future Telethon release that breaks it can only affect WebSocket users.
- **Proof is offline** (a local TLS WebSocket server plus a proxy that records every destination), **plus a version canary.** A live run on the real account, on the maintainer's go, closes what offline tests cannot.
- **New concerns surfaced** — the first two are designed out, the rest documented:
  - changing the login binding unconditionally would have broken every saved login;
  - certificate failures must not be retried;
  - a renamed door looks exactly like an outage;
  - Telegram refusing the door by policy could show up in the health events as an account problem.

## Finding

### Why this question exists

Some proxies send a connection out from their dedicated exit address only when the target is a **hostname**. Given an IP address, they send it out from a shared gateway address instead. Telethon, and therefore tgdata, connects to Telegram's data centres by IP, so such a proxy cannot carry an account from its own address.

Telegram also runs a WebSocket endpoint reached by hostname. A probe run on 2026-11-26, with no account, through such a proxy with IP targets refused, showed four things:
- **Every data centre works by name:** TLS verified, the WebSocket handshake answered, an encryption key was negotiated using Telethon's own wire format, and a ping was answered.
- **Every connection left from the proxy's dedicated address.**
- **Idle connections survive 150 seconds** and are cut by 300.
- **Two media-download names** (`kws2-1`, `kws4-1`) did not answer. Every other name did.

So the feature is possible. The question was how to add it so that tgdata stays as clean as it is.

### 1. The shape: one connection class, passed through the one factory

Telethon's client takes a `connection=` argument: a class it instantiates for every network connection it opens. Telethon builds a connection in four places — the main connection, a connection to another data centre for downloads, that connection's reconnect, and a content-delivery (CDN) client. **All four pass the data-centre number to the class.** So a class that turns "data centre 4" into `vesta.web.telegram.org` covers every path without touching Telethon's data-centre switching.

tgdata builds every client through one function, `ConnectionEngine._new_client`. tgdata's own documents call it "the single door", a separate thing from Telegram's WebSocket "door". When an account sets `transport = websocket`, that function adds `connection=<the WebSocket class>`. Nothing else in tgdata's client construction changes:
- the stack of request-level guards (read budget, join admission, heartbeat, health evidence, per-request flood threshold) sits above Telethon's sender, well above the connection;
- the strict options used by owned operations, the account pool and the stepwise login apply unchanged.

**Alternatives that were rejected:**
- **an out-of-process relay**, which would need the MTProto-proxy protocol, excluded from this issue;
- **patching Telethon globally**, which would change the default path;
- **a local SOCKS shim that rewrites IPs to names**, which duplicates what the data-centre number already gives.

Telethon 1.45.0 exposes exactly one in-process seam for this: its constructor asserts that `connection` is a class, and its proxy setting accepts only a dict or tuple.

### 2. What "never an IP" means, and how it is guaranteed

With `transport = websocket`, every connection the account's clients open goes to Telegram's WebSocket endpoint **by name**:
- logins, reads, verified operations, the pool, the worker, reconnects and downloads from other data centres;
- through the configured proxy with remote name resolution — tgdata already always asks the proxy to resolve names — or, with no proxy, directly by name.

It never connects to an IP, and it never falls back to the ordinary TCP transport.

**The guarantee is built into the code, not checked after the fact.**
- **The class.** Its constructor receives the IP and port Telethon would have used. It passes the *hostname* and port 443 to Telethon's own constructor instead, and the IP is dropped. Telethon's constructor simply stores whatever host it is given, so the object holds no IP at all. Even a future Telethon change that skipped the class's connect method could only ever reach a name, where it would fail the handshake loudly, not leak.
- **The opener.** The function that opens the WebSocket refuses a host that parses as an IP address. That is two lines, and it makes the lowest layer that opens a socket incapable of dialling an IP.

**An unknown data-centre number is an error, never a guess.** This includes Telethon's CDN path: the CDN client builds its connection with the parent's class, so a CDN data centre would raise immediately. Telethon never requests CDN downloads anyway, since nothing in its client sets the flag that enables them.

### 3. Configuration and the client factory

A new key in the account's `[Telegram]` config section:
- **`transport = tcp`** — the default, and what an absent key means;
- **`transport = websocket`.**

The config reader normalises the value once into the frozen `ConnectionConfig` record. Any other value raises a configuration error before any connection is attempted.

**Transport and proxy are independent settings.** `require_proxy` keeps its meaning: never connect without the proxy. A WebSocket transport *without* a proxy is allowed and connects directly by name. That is useful on networks that block Telegram's IP ranges but allow its web domain, and for local testing.

**The client factory imports the WebSocket class inside its `websocket` branch, not at the top of the module.** The reason is robustness. Plain `TgData` accepts any Telethon `>=1.45,<2.0`; only the account pool and the worker pin exactly 1.45.0. If a later 1.x release broke something the transport relies on, a top-level import would break every tgdata user. The local import confines the damage to accounts that chose WebSocket.

### 4. The connection class

It extends Telethon's `ConnectionTcpObfuscated`: Telethon's own obfuscated wire format, which the probe used successfully.
- **It overrides two methods and nothing else.**
- **Its constructor** maps the data-centre number to the hostname and calls the parent constructor with it. It forwards every other argument unchanged, so a Telethon patch release that adds an argument does not break construction.
- **Its connect method:**
  1. obtains a socket — through Telethon's own proxy code when a proxy is set, otherwise no socket, and the opener connects by name;
  2. calls the WebSocket opener;
  3. installs the resulting reader and writer;
  4. runs the same final three steps as Telethon's own connect: create the codec, write the obfuscation header, flush.

**Reusing Telethon's proxy code matters more than it first appears.** Inside that code, Telethon converts the proxy library's own error classes into Python's `ConnectionError`. That conversion is what makes proxy failures retryable network errors. Writing tgdata's own tunnel would lose it, or depend on it silently.

**Order matters inside connect.** Telethon's obfuscation layer captures the reader and writer at the moment the header is written. So the WebSocket reader and writer must be installed first.

### 5. The WebSocket opener

A small, hand-written function: about 100–150 lines, adapted from the probe, which is tested offline at every frame-size boundary and live. It uses only Python's standard library and **never imports Telethon**, so a future port to Telethon 2.x would rewrite only the class.

**What it does:**
- **TLS** with Python's default verification, and the hostname sent as the server name (SNI). The verification context can be injected, so tests can use their own certificate authority.
- **The handshake:** `GET /apiws` with `Sec-WebSocket-Protocol: binary`, requiring a `101` answer and a correct accept key. The `Origin: https://web.telegram.org` header is kept for now, because every recorded probe run used it.
- **The byte stream** Telethon reads: masked binary frames out; binary and continuation frames joined on the way in; pings answered; a close or end-of-stream turned into the "connection closed" error Telethon already expects.
- **One timeout** covers TLS and the handshake together.
- **No new dependency.** WebSocket libraries are message-oriented, and adapting one to the byte stream Telethon reads would need more machinery than the framing itself.

**No transport-level pings.** Telethon pings its main connection every 60 seconds on every connected client, including the strict ones that disable update handling. Connections to other data centres get no pings, but Telethon closes them after about 60–120 seconds idle. Either way no connection sits idle near the 150–300-second cut.

### 6. How failures are classified

Telethon retries a connection only when the error is an `IOError` (which `ConnectionError` is) or a timeout. The account pool stops on a `ValueError` and retries a `ConnectionError`. So the whole classification is a choice of exception type. No new retry logic, and no change to the pool or to the health module.

**Stop immediately** — a new tgdata error class in the `ValueError` family, like the existing proxy configuration error:
- an unknown `transport` value;
- an unknown data-centre number;
- a certificate that fails to verify, which signals interception or a broken trust store, never a passing glitch. Python raises this as an `OSError`, so it must be converted explicitly, or Telethon would retry it;
- an IP-address host given to the opener.

**Retried** (`ConnectionError`):
- a handshake that does not return `101`;
- connection resets;
- WebSocket protocol violations;
- the server closing the connection.

Proxy errors stay Telethon's own.

**Once a connection is established, the opener raises nothing but "connection closed" errors.** Telethon's receive loop handles those quietly. Anything else would be logged as an unexpected exception with a full traceback.

**Messages name the transport and the host, never a credential.** For example: "WebSocket transport: upgrade to vesta.web.telegram.org refused (HTTP 403)".

**Visibility of the cause.** When retries run out, Telethon raises its own generic "Connection to Telegram failed N times" error, without the original cause attached. The cause still appears in Telethon's warning lines. That is exactly how TCP failures behave today, and the errors that need operator action stop immediately with their own message.

### 7. The login checkpoint's binding

tgdata's stepwise login saves a checkpoint between "send the code" and "submit the code". It binds that checkpoint to a fingerprint of the settings that decide the account's network identity: api id, api hash, proxy, `require_proxy` and the device identity. The transport changes the address the conversation leaves from, just as the proxy does, so it belongs in that fingerprint.

**Adding it unconditionally would change the fingerprint of every existing checkpoint and break saved logins.** It is therefore added **only when it is not `tcp`**:
- every TCP account's fingerprint stays bit-identical, and a test pins today's value;
- switching the transport between the two login steps invalidates the checkpoint, as switching the proxy does.

### 8. Observability

- **The one-time route log line** gains "over WebSocket by name" for WebSocket accounts only. The TCP text is unchanged.
- **`health_check()`** reports the transport, which works even where logging is off, as in the worker.
- **Telethon already logs every connection's target at INFO,** `Connecting to vesta.web.telegram.org:443/…`, because its connection's text form uses the stored host. The README names this line as the operator's per-connection evidence that nothing went by IP. It needs no new code.

### 9. Tests

Everything except the live calibration is proven offline.

**The harness:**
- a local TLS WebSocket server with a test certificate authority;
- a recording proxy (HTTP CONNECT and SOCKS5) that logs every destination it is asked for. It extends the recording relay already used in tgdata's proxy tests.

**The checks:**
- **No IP on every path:** main connect, reconnect, a connection to another data centre, and the strict-option paths (owned operations, the account pool, the stepwise login). There is also a pool mixing a TCP account and a WebSocket account, each reaching only its own kind of destination.
  - Most cases replace only the WebSocket opener with a fake, never the proxy tunnel, so the destination record stays real. One test runs the real TLS server end to end.
- **Construction:** a connection built with an IP and data centre 2 holds `venus.web.telegram.org` and no IP.
- **Classification:** one test per failure class, through Telethon's real retry loop and the pool's real classifier. A server close mid-session logs a warning without a traceback.
- **The default is unchanged:** constructor arguments, route log text and login fingerprint, captured *before* any code changes.
- **No health events:** none of the transport's errors produces a health verdict. This pins an interface with the account-health feature that would otherwise be easy to break later.
- **A version canary,** in the style of tgdata's existing "run after any Telethon upgrade" test. It checks every Telethon internal the class relies on:
  - the connection constructor's signature;
  - the connect method's arguments;
  - the proxy code using the stored host and converting proxy-library errors;
  - the obfuscation layer capturing the reader and writer;
  - the four construction sites passing the data-centre number;
  - CDN downloads never being requested.

### 10. Documentation that must change in the same change

- **`connection_engine.py`'s comment calling remote name resolution "moot".** It becomes false: remote resolution is what carries the WebSocket hostname to the proxy.
- **The docstrings of the proxy parser and the client factory.**
- **A README section, "Connecting through Telegram's WebSocket door":**
  - the key;
  - what the proxy must allow (a tunnel to `*.web.telegram.org:443`);
  - "never an IP, no fallback";
  - the no-proxy case;
  - what failures look like;
  - how to confirm the transport is active;
  - the verified Telethon version.
- **The stepwise-login document's list of binding fields.**

New text says "network transport". The word "transport" already names request wrappers elsewhere in tgdata's docs, and those passages stay untouched.

### 11. The concern register

**Designed out:**
- **Saved logins breaking:** the conditional binding entry.
- **Certificate failures being retried:** they stop immediately.
- **A WebSocket problem harming TCP users:** the local import.
- **Accounts with different transports mixing in one process:** stateless class, per-call argument, tested.
- **Transport errors becoming health noise:** pinned by a test.

**Accepted and documented:**
- **The door is unpublished.** Telegram documents data-centre IPs, not these hostnames, and could change them.
  - A renamed door would look exactly like an outage: every attempt fails at the proxy's name lookup, and the account pool keeps cooling down and retrying.
  - The docs describe what that looks like.
- **An account whose earlier sessions came from a desktop app now connects through the web endpoint.** How Telegram treats that is unknown.
- **The web relays may have rate limits of their own.** Unverified.
- **The name map is calibrated on one day's probe,** from one machine through one proxy.
- **Login keys made over TCP should work over WebSocket,** because keys belong to a data centre, not a transport. Only a live run proves it.
- **Servers need a working certificate store,** or every WebSocket connection stops immediately with a clear error.
- **Telegram refusing the web endpoint by policy** might arrive as a Telegram error on the first request rather than as a network error. If its code is one the health module reports as "unclassified", it would look like an account problem. Operators should compare against `tcp` before reading such an event as an account verdict.

### 12. The ten open points

| # | Open point | Decision |
|---|---|---|
| 1 | Shape | A `ConnectionTcpObfuscated` subclass over a byte-stream adapter, passed through the one factory. |
| 2 | Where the name map lives | One fixed constant for DC 1–5, using the planet names. No per-account override, and an error for any other data centre. |
| 3 | Keep-alive | Telethon's 60 s keep-alive runs on strict clients too; no transport pings. Live confirmation of more than 300 s idle is in the live run. |
| 4 | Error taxonomy | By exception type: stop immediately (`ValueError` family) vs retry (`ConnectionError`). |
| 5 | `require_proxy` × WebSocket | Independent settings. WebSocket without a proxy is allowed and connects directly by name. |
| 6 | Login binding | `transport` joins it only when not `tcp`. |
| 7 | WebSocket client | Hand-written, standard library only, no new dependency. |
| 8 | False docs | The four corrections above. |
| 9 | Testing | The offline harness, a recording proxy on every path, the default-unchanged checks, the health check, and the canary. |
| 10 | Outside-world risks | The register above; the live run is the next measurement. |

## Next Actions

### MUST

- **Write the feature description from this finding.**
  - **What:** `desc.md` for issue #67 (problem, value, success criteria, scope, priority), taking the decisions above and the concern register as its premise.
  - **Who:** the maintainer and the assistant, following the project's contributing process (step 1).
  - **Gate:** once the maintainer has read this finding.
  - **Why:** the description is what the plan, the critique and the implementation inherit. Writing it from the decided design keeps them from re-opening settled points.
- **Capture today's default-path values before any code changes.**
  - **What:** record the `TelegramClient` constructor arguments, the route log text and the login fingerprint for a fixed TCP config.
  - **Who:** the implementer.
  - **Gate:** before the first code edit of the implementation.
  - **Why:** "the default is unchanged" can only be proven against values captured before the change.
- **Run the live calibration on the real account.**
  - **What:** with `transport = websocket`:
    - log in, read, and download from another data centre;
    - reuse an existing session made over TCP;
    - hold a connection idle for more than 300 seconds;
    - confirm every exit is from the dedicated address, and none by IP;
    - record any Telegram error that appears only under WebSocket.
  - **Who:** the maintainer runs it, or gives the go.
  - **Gate:** after the offline test suite passes, and only on the maintainer's explicit go.
  - **Why:** it is the only check of Telegram's behaviour toward the real account and `api_id`, which no offline test can reach.

### COULD

- **Settle whether the `Origin` header is needed.**
  - **What:** run the existing no-account probe with `--no-origin` for DC 1–5. If all five work, the header may be dropped. Otherwise keep it, and say why in a code comment.
  - **Who:** the maintainer, or on their go.
  - **Gate:** before the plan finalises the opener's header list.
  - **Why:** it removes one header that claims a web.telegram.org origin, or documents why it is required. Either way it is low stakes.
- **Quote the independent library's name map directly.**
  - **What:** open the third-party client library's data-centre list (gotd/td, `telegram/dcs/prod.go`) and quote it in `desc.md`. This inquiry saw it only as a search summary.
  - **Who:** the description's author.
  - **Gate:** while writing `desc.md`.
  - **Why:** it turns the name map's justification from a summary into checkable evidence.

### DEFERRED

- **Rotating between the two name families, or a constrained per-account hostname override.**
  - **Gate:** the live run, or a later probe, shows one name family failing while the other works.
  - **Why (if revived):** it would let accounts follow a renamed door without a release. Even then, prefer a visible one-constant change over silent rotation.
- **Matching the official web clients' wire format.**
  - **Gate:** the live run shows refusals that occur only over WebSocket.
  - **Why (if revived):** it becomes one variable among several to test, if the door treats tgdata differently.
- **A runtime Telethon version pin for the WebSocket transport.**
  - **Gate:** the version canary fails on a Telethon 1.x patch release.
  - **Why (if revived):** if Telethon's internals move often, refusing an untested version may be better than a broken transport. For now, construction-time naming means drift can only break the handshake, never leak an IP.

## Reasoning

**Why a connection class rather than anything else.** Telethon 1.45.0 offers exactly one in-process place to change how connections are made: the `connection=` class. The other shapes were each rejected for a specific reason:
- **an out-of-process relay** — the existing third-party relays speak the MTProto-proxy protocol, which tgdata refuses and this issue excludes;
- **a global patch** — it would change every client, the default included;
- **a local IP-to-name shim** — it would need the data-centre number, which the class already receives.

**Why the class names the data centre at construction, not at connect time.** Naming at construction makes "never an IP" a property of the object, not of one method, so Telethon drift cannot turn into a leak.

**Why reuse Telethon's proxy code.** It is a private method, but it does one thing tgdata needs: converting the proxy library's errors into retryable `ConnectionError`s. Owning the tunnel was rejected because it would either duplicate that conversion or rely on Telethon having already patched the proxy library globally — an order-dependent side effect.

**Why the error classification is by exception type.** Telethon's retry and the account pool both read only exception types. A design that marked errors with an attribute was rejected: neither reader would see it.

**Why tgdata does not write its own obfuscation.** Doing so would duplicate Telethon's obfuscation setup for no gain.

**Why no host override and no name rotation.** Both were proposed to survive Telegram renaming the door.
- **The override** needs a separately built class per configuration, because Telethon accepts only a class. That is permanent machinery for an event never observed, and a tgdata release does the same job.
- **Rotation** never happens on strict clients, which do not reconnect. On ordinary clients it would hide one family's outage behind retries that look healthy.

**Why the planet names.** The original reasoning — planet names were "the superset that worked" — was found wrong in critique. That superset was about the media-download names, which the design never uses. For the names it does use, the `kwsN` family worked just as well. The planet names stand because:
- an independent client library maps the same five planet names over the same endpoint;
- they read clearly in logs.

A formula (`kws{N}`) would remove the five-entry table, but would trade away that outside corroboration.

**Why the lazy import.** It was first proposed to keep the default path free of an extra import, which was too weak a reason, since importing a module changes no behaviour. It survived critique on a different ground: plain `TgData` is not pinned to one Telethon version, so a broken transport module must not be able to break TCP users.

**Why `Origin` is kept for now.** Every browser sends it, and every recorded probe run used it. Dropping it could make tgdata *more* unusual at the door, not less. Whether it is needed is cheap to test.

**Why no shared "network route" object.** Proposed as a from-scratch redesign. tgdata's existing frozen `ConnectionConfig` already is that object.

**Why not match the web clients' wire format.** Proposed to reduce the account's fingerprint. There is no evidence of which format the web clients use, or that it matters next to the account details sent on login.

**Why no health-field removal.** One proposal suggested Telethon's connect log line could replace `health_check()["transport"]`. It cannot: the worker runs with logging off. Both are kept.

## Open Questions

### Monitoring

- **Does the plain obfuscation header work on the real account for every data centre?** The probe used it without the data-centre number in the header. If the live run disagrees, the fix is local to the class (the probe already has the alternative header).
- **Do the web relays rate-limit per address,** and does Telegram treat a desktop-app `api_id` differently over the web endpoint? Observable in the live run.

### Blocked

- **The live calibration** — account behaviour, an existing TCP-made session over WebSocket, idle beyond 300 seconds — is blocked on the maintainer's explicit go to use the real account.

### Research Frontiers

- **How Telegram expresses a policy refusal of the web endpoint,** if it ever does: a network error, or a Telegram error on the first request. Only observation can show it.

### Refinement Triggers

- **The name map re-opens** if Telegram publishes WebSocket hostnames (derive from that source instead), or if the live run or a later probe shows a planet name failing.
- **The decision not to pin a Telethon version for this transport re-opens** if the version canary fails on a Telethon 1.x patch release.
- **Keeping `Origin` re-opens** when the `--no-origin` probe shows all five data centres work without it.
- **The plain obfuscation header re-opens** if the live run shows the door answering the handshake but not the encryption exchange.
