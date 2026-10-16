# Fresh PR51 revision8 probes

35/35 histories PASS on the first run. No product edit or fixture correction.
See ../pr-critic.md for the subject, premise/restart analysis and qualification limits.

`fresh_boundaries.py` uses actual owned PTYs, product input/CLI, LoginFlow, Telethon
1.45.0/SRP/native SQLite and ordinary-reader reopening, with controlled source replies
and sockets forbidden. It adds remapped editing/EOF, split128-byte Unicode passwords,
invalid-after-edit/typeahead, six EOF-plus-close-failure prompts, uncertainty
confirmations, source waits and terminal faults at source/file admission boundaries.

Run with the project Python3.11.10 environment and native controlling-terminal access:

```text
python devdocs/work/50-terminal-account-login/pr-probes-r3/fresh_boundaries.py
```

fresh-attempt-1.txt is the first runner output; per-case text files record actual
command output with synthetic data kept hidden. fresh-result.json records all35
outcomes, and fresh-verification.json confirms unchanged111 tested source hashes.
review-context.json identifies the exact base/head/tree; reviewed.diff is the
published product patch, which matches local content after hunk-label normalization.

An injected intermediate restore failure correctly releases no value and remains
physically un-restored before fixture repair. A source-induced unsupported mode is
preserved on refusal; it is deliberately different from initial modes. Neither is
mislabelled as successful restoration. All case deadlines treat killed children as
failures. No live Telegram or additional host/runtime claim follows.

After execution, per-case text transcripts were normalized from PTY CRLF and
trailing prompt spaces for git whitespace hygiene. raw-transcripts.json preserves
the exact pre-normalization text and SHA256 for every case. No probe, product,
expectation or observed outcome changed; no rerun was needed.
