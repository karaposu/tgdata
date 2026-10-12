# Prebuild fixture correction — 2026-10-13

Attempt1 passed46/46 original+new groups and workers33/33+25/25. Matrix audit added
backfill recovery and cancelled raw settlement. Attempt2 passed47/48 plus both workers.
The sole failure was the new recovery fixture expecting charge200 after cancelling
the first SDK request. Telethon1.45 `_MessagesIter` caps a page at100, so that fixture
had exercised only one reserved page. This is a local input mistake, not a changed
ownership or budget premise.

Corrected the input: an actual100-message response precedes the pending second page.
The original expected charge200, unchanged account state, exact recovery, cursor100
and before/after commit assertions remain unchanged. No runtime candidate change,
expectation weakening, manufactured charge or undocumented repair. This also probes
that recovering a cancelled attempt does not acknowledge its observed prefix.
Full combined gate rerun, not only this function. Original attempts/hashes retained.
