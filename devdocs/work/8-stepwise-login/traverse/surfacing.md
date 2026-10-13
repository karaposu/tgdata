---
model: gpt-6-astra
effort: max
---
# Surfacing — authentication state and ownership

## User Input
Territory: current repository c4e6eac and installed Telethon1.45/auth documentation. Purpose: _branch.md I1 and all three considered articulations. Re-invocation uses ../surfacing.md and the same-session source workspace; refine from triage reach to auth-state/ownership interfaces.

## Reception
Artifact, signal-first, explicit bounded. Boundary discovery not needed. Prior-tagged source content retained; newly inspected SRP, raw auth signatures, error inheritance and health isolation included. No candidate selected.

## Traversal Trace

### T1
- Region: framing
- Item: `_branch.md`; label: I1; V1–V3
- Relevance: core; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-13T20:45:23.544874+00:00"}`

### T2
- Region: request
- Item: `../source-input.md`; label: phone/code/password; existing session/proxy
- Relevance: core; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-13T20:42:36.097133+00:00"}`

### T3
- Region: auth-source
- Item: `telethon/client/auth.py`; label: send_code_request; sign_in; _on_login
- Relevance: core; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-03T09:09:32.890427+00:00"}`

### T4
- Region: auth-source
- Item: `telethon/client/users.py`; label: _call; get_me; migration
- Relevance: core; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-03T09:09:32.893062+00:00"}`

### T5
- Region: auth-source
- Item: `telethon/client/telegrambaseclient.py`; label: connect; _switch_dc; _save_states_and_entities
- Relevance: core; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-03T09:09:32.892326+00:00"}`

### T6
- Region: auth-source
- Item: `telethon/password.py`; label: SRP compute_check
- Relevance: core; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-03T09:09:32.887389+00:00"}`

### T7
- Region: transport
- Item: `tgdata/connection_engine.py`; label: _new_client; _authorization_problem
- Relevance: core; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-13T20:35:19.729639+00:00"}`

### T8
- Region: transport
- Item: `tgdata/account_operation.py`; label: _disconnect_owned
- Relevance: core; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-13T20:35:19.727330+00:00"}`

### T9
- Region: state
- Item: `tgdata/session_store.py`; label: dump/restore; save mutation guard
- Relevance: core; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-13T20:35:19.735676+00:00"}`

### T10
- Region: state
- Item: `telethon/sessions/string.py`; label: StringSession credential representation
- Relevance: sub; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-03T09:09:32.902653+00:00"}`

### T11
- Region: isolation
- Item: `tgdata/health.py`; label: isolate_call; request evidence
- Relevance: sub; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-13T20:35:19.730640+00:00"}`

### T12
- Region: prior-consumers
- Item: `tgdata/pool_lifecycle.py`; label: owned child outcome; stop/join
- Relevance: sub; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-13T20:35:19.733315+00:00"}`

### T13
- Region: prior-consumers
- Item: `tgdata/pool_result.py`; label: caller-retained data
- Relevance: sub; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-13T20:35:19.734047+00:00"}`

### T14
- Region: public-contract
- Item: `README.md`; label: Authentication; store; proxy/device
- Relevance: sub; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-13T20:35:19.704860+00:00"}`

### T15
- Region: public-contract
- Item: `tgdata/tgdata.py`; label: legacy authentication/public signatures
- Relevance: sub; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-13T20:35:19.751303+00:00"}`

### T16
- Region: regression
- Item: `tgdata/smoke_tests/test_15_login_checks.py`; label: ordinary no-code behavior
- Relevance: sub; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-13T20:35:19.741582+00:00"}`

### T17
- Region: regression
- Item: `tgdata/smoke_tests/test_17_session_store.py`; label: opaque store/readback/native cleanup
- Relevance: sub; confidence: HIGH
- Recency annotation: `{"source": "filesystem", "value": "2026-10-13T20:35:19.742032+00:00"}`

### T18
- Region: vendor
- Item: `https://core.telegram.org/api/auth`; label: auth key association; challenge constructors; test DCs
- Relevance: core; confidence: HIGH
- Recency annotation: `{"source": "none", "value": null}`

### T19
- Region: vendor
- Item: `https://core.telegram.org/method/auth.signIn`; label: authorization/registration/2FA responses
- Relevance: sub; confidence: HIGH
- Recency annotation: `{"source": "none", "value": null}`

### T20
- Region: vendor
- Item: `https://docs.telethon.dev/en/stable/concepts/sessions.html`; label: portable session-secret semantics
- Relevance: sub; confidence: HIGH
- Recency annotation: `{"source": "none", "value": null}`

## State Summary
Territory/purpose echo: Reception and _branch.md; all V1–V3 present. Workspace populated: true at 2026-10-13T20:52:05.699847+00:00; relevant bodies/signatures read, prior whole-module context retained.
Coverage: every listed region confirmed at the named contract/method resolution. SDK/server responses remain documentary until independently probed; no live service observation is claimed.
Confirmed absent: public multi-step login and incomplete-login persistence/coordination contract in current tgdata; an auth-specific test suite.
Concept names with provenance: challenge request/hash (T3); auth key/DC (T5,T9,T10); authorization result and post-login setup (T3); SRP proof (T6); configured route/device (T7); physical retirement (T8); final credential store (T9); neutral health scope (T11); component/caller outcome (T12,T13); caller-owned persistence (T1,T2); alternative server challenge (T18,T19). All labels are vocabulary/structural references, not adjudicated relationships.
Recency distribution:
```json
{
  "framing": {
    "newest": "2026-10-13T20:45:23.544874+00:00",
    "oldest": "2026-10-13T20:45:23.544874+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "request": {
    "newest": "2026-10-13T20:42:36.097133+00:00",
    "oldest": "2026-10-13T20:42:36.097133+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "auth-source": {
    "newest": "2026-10-03T09:09:32.893062+00:00",
    "oldest": "2026-10-03T09:09:32.887389+00:00",
    "no-mtime-count": 0,
    "total-items": 4
  },
  "transport": {
    "newest": "2026-10-13T20:35:19.729639+00:00",
    "oldest": "2026-10-13T20:35:19.727330+00:00",
    "no-mtime-count": 0,
    "total-items": 2
  },
  "state": {
    "newest": "2026-10-13T20:35:19.735676+00:00",
    "oldest": "2026-10-03T09:09:32.902653+00:00",
    "no-mtime-count": 0,
    "total-items": 2
  },
  "isolation": {
    "newest": "2026-10-13T20:35:19.730640+00:00",
    "oldest": "2026-10-13T20:35:19.730640+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "prior-consumers": {
    "newest": "2026-10-13T20:35:19.734047+00:00",
    "oldest": "2026-10-13T20:35:19.733315+00:00",
    "no-mtime-count": 0,
    "total-items": 2
  },
  "public-contract": {
    "newest": "2026-10-13T20:35:19.751303+00:00",
    "oldest": "2026-10-13T20:35:19.704860+00:00",
    "no-mtime-count": 0,
    "total-items": 2
  },
  "regression": {
    "newest": "2026-10-13T20:35:19.742032+00:00",
    "oldest": "2026-10-13T20:35:19.741582+00:00",
    "no-mtime-count": 0,
    "total-items": 2
  },
  "vendor": {
    "newest": null,
    "oldest": null,
    "no-mtime-count": 3,
    "total-items": 3
  }
}
```

## Frontier
Probe SDK resend/post-auth/migration behavior and actual session/SRP/lifetime composition. Resolve whether portable state means completed-step restoration or stronger in-flight crash/retry ownership. Define caller storage/publication responsibilities and unsupported server challenges. No frontier is silently treated as already tested.

## Telemetry
Four traversal cycles: framing/state; SDK auth/transport; ownership/isolation; consumers/vendor. Items:20; tags:{'core': 10, 'sub': 10}; mtime:17; no mtime:3.
No item filtered by recency, no uncertain item excluded, no overload trigger. LAYER1 coverage/territory/desync/metadata-bias checks and LAYER2 purpose/interpretive-overstep checks pass. No solution, stable cross-item model or action ranking emitted.
Manual structural check passed: trace fields, derived coverage/absence/concepts/recency/workspace, frontier and telemetry. Repository checker absent.
Verdict: PROCEED.
