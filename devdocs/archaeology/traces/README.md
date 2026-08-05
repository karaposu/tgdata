# Runtime Traces — Index

Expert annotated walkthroughs of specific runtime behaviors in `tgdata`. Each trace follows a behavior from its entry point to its terminal state, with judgment on design, risk, and improvement direction. Analysis is grounded in actual code behavior (file:line references throughout), not names.

Read `../intro2codebase.md` first for the architectural map.

| # | Category | Behavior traced |
|---|----------|-----------------|
| [trace_1](trace_1.md) | Lifecycle | Telegram client: create → connect-with-retry → per-op teardown → close |
| [trace_2](trace_2.md) | Lifecycle | Real-time event-handler registration and firing |
| [trace_3](trace_3.md) | Data transformation | Message → `MessageData` → DataFrame → CSV/JSON |
| [trace_4](trace_4.md) | Data transformation | DataFrame → statistics / metrics report |
| [trace_5](trace_5.md) | Integration boundary | Auth: config → `client.start` → `.session` persistence |
| [trace_6](trace_6.md) | Integration boundary | Fetch: entity resolution + `iter_messages` streaming |
| [trace_7](trace_7.md) | Decision / routing | Fetch iteration-parameter routing (polling vs historical vs date) |
| [trace_8](trace_8.md) | Decision / routing | Client acquisition: pool vs primary + health-check gate |
| [trace_9](trace_9.md) | Error / recovery | FloodWait rate-limit catch → sleep → recursive retry |
| [trace_10](trace_10.md) | Error / recovery | Polling message-skipping + `seen_message_ids` dedup |
| [trace_11](trace_11.md) | Error / recovery | Silent message drop on missing sender / swallowed exception |
| [trace_12](trace_12.md) | Cross-cutting | Rate limiting spread across three locations |
| [trace_13](trace_13.md) | Cross-cutting | Progress tracking mechanism |

**Recurring themes across traces** (each is expanded where it surfaces):
- The **connection contradiction** — a persistent/pooled client design defeated by `async with client:` teardown on every call (traces 1, 6, 8, 9, 12).
- **Silent data loss** — three independent paths where messages vanish with no error: `limit=None → 100` cap (6, 7), polling `min_id` skips (10), missing-sender drop (11).
- **Refactor residue** — vestigial pooling, unused `_metrics`, compatibility hacks (1, 8, 12).
