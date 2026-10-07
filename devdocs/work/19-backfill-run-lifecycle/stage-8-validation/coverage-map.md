---
model: gpt-6-astra
effort: max
status: PASS-scoped-local-and-live-evidence
---
# Stage 8 case-to-evidence map

All named tests below passed in the supported regression at product `405218e`.
LOCAL means actual SQLite/SDK with synthetic transport and blocked sockets. D means
the actual public/Telegram/receiver composition in [Gate D](../validation/gate-d.md);
A/B/C retain their stated scopes. No deployment or natural server-error claim is inferred.

| Case | Named executed test (test_ prefix retained) | Actual composed evidence and limits |
|---|---|---|
| C01 — Start reply lost | [30: test_creation_real_commit_exit_pair](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D main-local original creation retry; test24 relative-window forbidden-clock retry |
| C02 — Changed input reuses creation identity | [24: test_changed_input_and_active_successor_conflict](../../../../tgdata/smoke_tests/test_24_backfill_state.py) | LOCAL immutable-intent refusal; common engine revalidated through public retries |
| C03 — Deliberate identical new job | [30: test_successor_real_commit_exit_pair_keeps_old_receipt_read_only](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D controls: four real equal-hash generations |
| C04 — Forgotten old start | [28: test_retained_accepted_receipt_and_previous_cancel_are_read_only_then_pruned](../../../../tgdata/smoke_tests/test_28_backfill_controls.py) | D controls: first generation pruned, old receipt refused |
| C05 — Known state unavailable | [30: test_missing_malformed_known_state_and_cleanup_preserve_uncertainty](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | LOCAL public missing/malformed/file-loss and cleanup boundaries |
| C06 — Old resume response arrives last | [30: test_opposing_controls_and_delayed_resume_are_revision_ordered](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D controls: delayed accepted resume arrives after newer pause |
| C07 — Unaccepted stale resume | [28: test_stale_resume_prepare_and_forgotten_command_refuse](../../../../tgdata/smoke_tests/test_28_backfill_controls.py) | D controls: stale resume refuses; original context retained |
| C08 — Two conflicting controls | [30: test_opposing_controls_and_delayed_resume_are_revision_ordered](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D controls: actual shared-load/CAS barrier accepts exactly one decision |
| C09 — Completion before cancellation | [30: test_ack_real_commit_exit_pair_follows_receiver](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D controls: completion-first then cancellation reports terminal |
| C10 — Cancellation before final receipt | [30: test_late_final_result_cancel_order_and_equal_hash_successor](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D controls: cancellation-first then final receiver/ack remains cancelled |
| C11 — Final receipt while paused | [30: test_control_real_commit_exit_pair_preserves_delivery](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D prebuild and controls: exact final ack completes while paused |
| C12 — Imported midpoint | [24: test_imported_origin_is_not_acceptance_or_exhaustion](../../../../tgdata/smoke_tests/test_24_backfill_state.py) | D prebuild/unknown/photo: imported after13 completes declared photo tail only |
| C13 — Daily progress cannot seed fresh backfill silently | [29: test_daily_and_backfill_progress_are_separate_and_no_auto_namespace_exists](../../../../tgdata/smoke_tests/test_29_backfill_public.py) | D main: fresh history after0; daily starts at independent recent origin; rows isolated |
| C14 — Full last batch followed by refusal | [25: test_exact_full_batch_needs_real_end_not_length](../../../../tgdata/smoke_tests/test_25_backfill_delivery.py) | D photo: full one-record batch then local refusal remains incomplete; later real end |
| C15 — Missing local artifact after receiver acceptance | [30: test_media_receipt_custody_ack_without_source_bytes_and_health](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D photo: durable receiver bytes precede source removal and actual ack-commit exit |
| C16 — Live pending receipt outlives history policy | [28: test_retired_equal_hash_receipt_never_accepts_successor](../../../../tgdata/smoke_tests/test_28_backfill_controls.py) | C retention matrix and D controls: prior histories retire/prune without expiring current pending |
| C17 — Budget ends after usable prefix | [29: test_public_budget_prefix_and_failed_prefix_save_keep_provenance](../../../../tgdata/smoke_tests/test_29_backfill_public.py) | C actual bounded budget exhaustion; D 100-record locally interrupted prefix with retained charges |
| C18 — Crash after possible send | [30: test_admission_real_commit_exit_pair_never_sends](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D unknown-source: actual raw return/exit81, confirmed child death then recovery |
| C19 — Restart during known wait | [29: test_clock_minimum_survives_public_calls_and_close](../../../../tgdata/smoke_tests/test_29_backfill_public.py) | D main-local: restart preserves deadline, decreasing early wait; later real reads >=12s |
| C20 — Untrustworthy time evidence | [27: test_clock_regression_and_invalid_ns_refuse_without_admission](../../../../tgdata/smoke_tests/test_27_backfill_pacing.py) | LOCAL UTC/monotonic fault boundaries; trusted UTC after restart remains deployment assumption |
| C21 — Commit succeeded but response failed | [30: test_cancelled_publication_and_ack_reply_reopen_actual_effect](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | All nine test30 commit exit pairs; D actual receiver/source/recovery/ack exits; no power-loss claim |
| C22 — Paused, pending and rate-limited together | [28: test_paused_failed_budget_prefix_replays_and_ack_preserves_wait_and_failure](../../../../tgdata/smoke_tests/test_28_backfill_controls.py) | C actual combined paused budget prefix; D independently repeats public pause/delivery/failure boundaries |
| C23 — Empty and nonempty exhausted scope | [30: test_empty_end_real_commit_exit_pair](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D main final partial/ack and photo actual empty end without fake receipt |
| C24 — Failure before a usable prefix | [25: test_no_prefix_failure_settles_without_end_or_cursor_advance](../../../../tgdata/smoke_tests/test_25_backfill_delivery.py) | D photo local pre-send failure: no pending/end/cursor advance; no natural server denial claimed |
| C25 — Prefix save also fails | [30: test_failed_prefix_and_publication_keep_source_provenance_then_recover](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | LOCAL public SDK error plus failed real publication, unchanged health during recovery/wait |
| C26 — Admission write failed or uncertain | [30: test_admission_real_commit_exit_pair_never_sends](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D unknown attempt refuses new prepare; LOCAL before/after admission exits send zero |
| C27 — Late source result after control mutation | [30: test_late_final_result_cancel_order_and_equal_hash_successor](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D controls: real result held before publication preserves newer pause; LOCAL late cancellation |
| C28 — Recovery while old reader lives | [29: test_one_cached_engine_preserves_busy_source_and_late_control](../../../../tgdata/smoke_tests/test_29_backfill_public.py) | D controls: busy recover/abandon refuse; parent confirms each owned worker exit |
| C29 — Corrupt pending artifact | [30: test_media_receipt_custody_ack_without_source_bytes_and_health](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D photo: corrupt disposable copy refuses unchanged, no refetch or health recovery |
| C30 — Wrong collection, destination or run receipt | [25: test_wrong_and_unknown_receipts_preserve_pending](../../../../tgdata/smoke_tests/test_25_backfill_delivery.py) | B wrong destination/run/collection; D controls same-hash full-scoped receipts; test29 receiver scope |
| C31 — Duplicate latest ack with newer pending | [25: test_scoped_ack_duplicate_and_zero_pause_continuation](../../../../tgdata/smoke_tests/test_25_backfill_delivery.py) | B latest same-run duplicate preserves newer pending; D prior-run duplicate preserves successor pending |
| C32 — Explicit abandonment and successor | [30: test_abandon_real_commit_exit_pair_retires_receipt](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D controls: cancel/abandon after quiescence; unchanged cursor, distinct successor |
| C33 — Local public operations and health | [29: test_local_operations_preserve_prior_health_and_make_no_calls](../../../../tgdata/smoke_tests/test_29_backfill_public.py) | D all socket/config-blocked local workers and operation-tagged live RPC traces; injected fixture labeled |
| C34 — Legacy compatibility and separate collections | [29: test_daily_and_backfill_progress_are_separate_and_no_auto_namespace_exists](../../../../tgdata/smoke_tests/test_29_backfill_public.py) | 357 actual supported offline passes; D main daily/history state and receiver integration |
| C35 — Delayed prepare after acknowledgment | [25: test_scoped_ack_duplicate_and_zero_pause_continuation](../../../../tgdata/smoke_tests/test_25_backfill_delivery.py) | D main-local explicitly refuses original pre-ack prepare context without source |
| C36 — Delayed prepare after pause/resume | [30: test_opposing_controls_and_delayed_resume_are_revision_ordered](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D controls stale prepare after accepted controls refuses with unchanged pending |
| C37 — Absent slot is not unknown retry permission | [29: test_unknown_start_and_run_never_bootstrap](../../../../tgdata/smoke_tests/test_29_backfill_public.py) | LOCAL public absent slot: retry/status refuse; test30 before-creation exit retains absence |
| C38 — Intentional retry after settled failure | [30: test_failed_prefix_and_publication_keep_source_provenance_then_recover](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | C real allowance recheck; D photo explicit later retry after failed follow-up and actual >=12s wait |
| C39 — Recovery reply lost | [30: test_recovery_real_commit_exit_pair_preserves_original_command](../../../../tgdata/smoke_tests/test_30_backfill_integration.py) | D recovery commit exit82 then exact retry/deadline; next real read >=12s |
| C40 — Missing independent oracle or source drift | [24: test_window_and_clock_failures_are_local](../../../../tgdata/smoke_tests/test_24_backfill_state.py) | A rejected non-group/undersized fixture; D direct qualified sets frozen before reads, unchanged counts; drift guard retained |
| C41 — Real SDK and caller pagination | [25: test_short_slice_is_not_itself_source_exhaustion](../../../../tgdata/smoke_tests/test_25_backfill_delivery.py) | D 250 exact records in120/120/10; actual second SDK pages; source differs from independent descending oracle |
| C42 — Exact date selection and media mode | [25: test_fresh_relative_query_uses_original_window_after_clock_moves](../../../../tgdata/smoke_tests/test_25_backfill_delivery.py) | A/B full boundary matrix; D fresh/imported closed scopes and independent real photo digest |
| C43 — Invalid or incompatible saved state | [24: test_malformed_outer_and_request_refused](../../../../tgdata/smoke_tests/test_24_backfill_state.py) | Strict codec suites plus test30 public malformed/missing state; no bootstrap or repair |
| C44 — Input, scope and identity normalization | [24: test_input_and_portable_identity](../../../../tgdata/smoke_tests/test_24_backfill_state.py) | Strict input/counter/codec suites plus test29 typed public exports/required args/bad address refusal |

All 12 invariants are tied to these histories in the original matrix and the
[whole-feature audit](review-readiness.md). One active source reader, durable external
receiver acceptance, trusted restart UTC and equivalent custom-backend guarantees remain
explicit deployment preconditions. No distributed ownership, source mutation, edit/deletion
reconciliation, arbitrary history retention or other SDK version is certified.
