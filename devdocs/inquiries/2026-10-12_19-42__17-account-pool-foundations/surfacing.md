---
model: gpt-6-astra
effort: max
---
# Surfacing — #17 foundations

## User Input

`_branch.md`: examine the actual revision history, causal gaps and potentially
simpler concepts behind #17, preserving all five considered articulations.

## Reception

Artifact case; signal-first; explicit-bounded territory: #17 historical inquiry,
plans/reviews, pool runtime and qualification, with current #7/#10 comparison paths.
Boundary-discovery not needed. Relevance follows content versus this inquiry's
purpose; checkout mtimes are descriptive metadata, never chronological evidence.
Git/issue chronology must be read from its own records.

## Traversal Trace

| Ordinal | Region | Item identifier | Relevance | Confidence | Recency annotation | Step note |
|---|---|---|---|---|---|---|
| S01 | framing | `devdocs/inquiries/2026-10-12_19-42__17-account-pool-foundations/_branch.md` | core | HIGH | filesystem: 2026-10-12T16:43:44.500733+00:00 | purpose input |
| S02 | history | `devdocs/work/17-account-pool/HANDOFF.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.301521+00:00 | read in full |
| S03 | history | `devdocs/work/17-account-pool/desc.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.302096+00:00 | read in full |
| S04 | history | `devdocs/work/17-account-pool/retirement-rework/desc.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.306769+00:00 | read in full |
| S05 | prior inquiry | `devdocs/work/17-account-pool/traverse/finding.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.372957+00:00 | read in full |
| S06 | plans | `devdocs/work/17-account-pool/step_by_step_impl_plan.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.359031+00:00 | read in full |
| S07 | plans | `devdocs/work/17-account-pool/critic.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.301822+00:00 | read in full |
| S08 | plans | `devdocs/work/17-account-pool/retirement-rework/plan.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.339147+00:00 | read in full |
| S09 | plans | `devdocs/work/17-account-pool/retirement-rework/critic.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.306421+00:00 | read in full |
| S10 | rejected review | `devdocs/work/17-account-pool/pr-critic.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.305183+00:00 | read in full |
| S11 | history | `git log 95ed4c7..71502e5 -- tgdata/account_pool.py tgdata/pool_source.py`; work-folder commit history | core | HIGH | none: null | Git objects; revision/implementation checkpoints enumerated |
| S12 | remote scope | `https://github.com/karaposu/tgdata/issues/17` | core | HIGH | none: null | fetched current state/description/review record |
| S13 | remote scope | `https://github.com/karaposu/tgdata/pull/26` | core | HIGH | none: null | current rejected PR scope |
| S14 | runtime | `tgdata/pool_source.py` | core | HIGH | filesystem: 2026-10-12T16:40:23.401420+00:00 | complete source and lifecycle implementation |
| S15 | runtime | `tgdata/account_pool.py` | core | HIGH | filesystem: 2026-10-12T16:40:23.390590+00:00 | complete controller implementation |
| S16 | runtime | `tgdata/pool_state.py` | core | HIGH | filesystem: 2026-10-12T16:40:23.401696+00:00 | complete state implementation |
| S17 | delivery | `tgdata/progress_facade.py` | sub | HIGH | filesystem: 2026-10-12T16:40:23.402355+00:00 | complete shared facade |
| S18 | rejected review | `devdocs/work/17-account-pool/pr-critic-probes.py` | core | HIGH | filesystem: 2026-10-12T16:40:23.304676+00:00 | complete reproduction code |
| S19 | rejected review | `devdocs/work/17-account-pool/pr-critic-probes.txt` | core | HIGH | filesystem: 2026-10-12T16:40:23.304924+00:00 | complete saved observations |
| S20 | public contract | `docs/account_pool.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.381387+00:00 | complete public contract |
| S21 | prior inquiry | `devdocs/work/17-account-pool/traverse/docarchive/critique_iter1.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.368661+00:00 | complete earlier adversarial record |
| S22 | prior inquiry | `devdocs/work/17-account-pool/traverse/docarchive/critique.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.367962+00:00 | complete second iteration record |
| S23 | qualification | `devdocs/work/17-account-pool/implementation.md` | sub | HIGH | filesystem: 2026-10-12T16:40:23.302618+00:00 | complete first delivery account |
| S24 | qualification | `devdocs/work/17-account-pool/retirement-rework/verification.md` | core | HIGH | filesystem: 2026-10-12T16:40:23.358251+00:00 | complete integrated verification record |
| S25 | qualification | `tgdata/smoke_tests/test_31_account_pool.py` | core | HIGH | filesystem: 2026-10-12T16:40:23.416422+00:00 | fixtures and complete relevant outcome/lifetime cases; full function index |
| S26 | adjacent ownership | `tgdata/account_operation.py` | sub | HIGH | filesystem: 2026-10-12T16:40:23.390196+00:00 | complete accepted temporary owner |
| S27 | adjacent ownership | `tgdata/owned_health.py` | sub | HIGH | filesystem: 2026-10-12T16:40:23.401003+00:00 | complete fixed-owner observer implementation |
| S28 | health | `tgdata/health.py` | core | HIGH | filesystem: 2026-10-12T16:40:23.395912+00:00 | retained full implementation context; refreshed awaited callback delivery |
| S29 | source | `tgdata/budget_client.py` | sub | HIGH | filesystem: 2026-10-12T16:40:23.392748+00:00 | complete actual admission adapter |
| S30 | source | `tgdata/batch_engine.py` | sub | HIGH | filesystem: 2026-10-12T16:40:23.391992+00:00 | complete fetch_batch and cancellation-prefix seam |
| S31 | current dev | `2ddb852:tgdata/worker_engine.py`; `68f6bbd..2ddb852:account_operation/connection_engine diff` | sub | HIGH | none: null | complete worker executor and relevant shared changes |

## State Summary

**Territory:** #17 original inquiry, original/scoped planning and qualification,
rejected PR, source/controller/state/progress implementations and relevant accepted
#7/#10 comparison surfaces. **Purpose:** test the revision-cause and simplifying-
concept readings in `_branch.md`; no redesign is selected by relevance tagging.

### Coverage map

- **framing:** confirmed at recorded item resolution; aggregate core; entries S01.
- **history:** confirmed at recorded item resolution; aggregate core; entries S02,S03,S04,S11.
- **prior inquiry:** confirmed at recorded item resolution; aggregate core; entries S05,S21,S22.
- **plans:** confirmed at recorded item resolution; aggregate core; entries S06,S07,S08,S09.
- **rejected review:** confirmed at recorded item resolution; aggregate core; entries S10,S18,S19.
- **remote scope:** confirmed at recorded item resolution; aggregate core; entries S12,S13.
- **runtime:** confirmed at recorded item resolution; aggregate core; entries S14,S15,S16.
- **delivery:** confirmed at recorded item resolution; aggregate sub; entries S17.
- **public contract:** confirmed at recorded item resolution; aggregate core; entries S20.
- **qualification:** confirmed at named interfaces/cases; aggregate core; entries S23,S24,S25.
- **adjacent ownership:** confirmed at recorded item resolution; aggregate sub; entries S26,S27.
- **health:** confirmed at named interfaces/cases; aggregate core; entries S28.
- **source:** confirmed at named interfaces/cases; aggregate sub; entries S29,S30.
- **current dev:** confirmed at recorded item resolution; aggregate sub; entries S31.

**Confirmed absent at searched resolution:** no implemented revision3 or second
rejected PR artifact on the71502e5 branch; no pool runtime update in current dev's
post68f6bbd history. These are repository/issue-state observations, not a conclusion
about the design's soundness. Native multi-account live evidence remains unconfirmed,
not “confirmed absent from reality.”

### Concept names (no causal interpretation)

- `{name: AccountPool, type: structural-reference, provenance: S15}`
- `{name: owned source, type: structural-reference, provenance: S14}`
- `{name: completed source outcome, type: vocabulary, provenance: S14}`
- `{name: observer cancellation, type: vocabulary, provenance: S10}`
- `{name: callback descendant, type: vocabulary, provenance: S10}`
- `{name: retained cleanup, type: vocabulary, provenance: S09}`
- `{name: durable attempt permission, type: vocabulary, provenance: S16}`
- `{name: client retirement block, type: structural-reference, provenance: S14}`
- `{name: caller cancellation, type: vocabulary, provenance: S25}`
- `{name: wait dependency cycle, type: vocabulary, provenance: S18}`
- `{name: budget admission, type: structural-reference, provenance: S29}`
- `{name: pending delivery acknowledgment, type: vocabulary, provenance: S17}`
- `{name: fixed-owner health, type: structural-reference, provenance: S27}`
- `{name: local bounded collector, type: structural-reference, provenance: S31}`
- `{name: two-account live E1, type: vocabulary, provenance: S06}`

### Recency distribution

Descriptive UTC filesystem mtimes are mostly checkout timestamps, not edit chronology.
No old item was filtered or demoted. Git objects/remote records have explicit none/null.

```json
{
  "framing": {
    "newest": "2026-10-12T16:43:44.500733+00:00",
    "oldest": "2026-10-12T16:43:44.500733+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "history": {
    "newest": "2026-10-12T16:40:23.306769+00:00",
    "oldest": "2026-10-12T16:40:23.301521+00:00",
    "no_mtime_count": 1,
    "total_items": 4
  },
  "prior inquiry": {
    "newest": "2026-10-12T16:40:23.372957+00:00",
    "oldest": "2026-10-12T16:40:23.367962+00:00",
    "no_mtime_count": 0,
    "total_items": 3
  },
  "plans": {
    "newest": "2026-10-12T16:40:23.359031+00:00",
    "oldest": "2026-10-12T16:40:23.301822+00:00",
    "no_mtime_count": 0,
    "total_items": 4
  },
  "rejected review": {
    "newest": "2026-10-12T16:40:23.305183+00:00",
    "oldest": "2026-10-12T16:40:23.304676+00:00",
    "no_mtime_count": 0,
    "total_items": 3
  },
  "remote scope": {
    "newest": null,
    "oldest": null,
    "no_mtime_count": 2,
    "total_items": 2
  },
  "runtime": {
    "newest": "2026-10-12T16:40:23.401696+00:00",
    "oldest": "2026-10-12T16:40:23.390590+00:00",
    "no_mtime_count": 0,
    "total_items": 3
  },
  "delivery": {
    "newest": "2026-10-12T16:40:23.402355+00:00",
    "oldest": "2026-10-12T16:40:23.402355+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "public contract": {
    "newest": "2026-10-12T16:40:23.381387+00:00",
    "oldest": "2026-10-12T16:40:23.381387+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "qualification": {
    "newest": "2026-10-12T16:40:23.416422+00:00",
    "oldest": "2026-10-12T16:40:23.302618+00:00",
    "no_mtime_count": 0,
    "total_items": 3
  },
  "adjacent ownership": {
    "newest": "2026-10-12T16:40:23.401003+00:00",
    "oldest": "2026-10-12T16:40:23.390196+00:00",
    "no_mtime_count": 0,
    "total_items": 2
  },
  "health": {
    "newest": "2026-10-12T16:40:23.395912+00:00",
    "oldest": "2026-10-12T16:40:23.395912+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "source": {
    "newest": "2026-10-12T16:40:23.392748+00:00",
    "oldest": "2026-10-12T16:40:23.391992+00:00",
    "no_mtime_count": 0,
    "total_items": 2
  },
  "current dev": {
    "newest": null,
    "oldest": null,
    "no_mtime_count": 1,
    "total_items": 1
  }
}
```

### Frontier and handoff

- Interpret which authority each observed failure crosses; repetition count alone
  has not established a common cause. Source outcome and physical task termination
  require separate examination in Sensemaking.
- Re-run actual pool/SDK/SQLite reproductions before treating the historical probes
  as current behavioral evidence. Then identify counterexamples to a broader cause.
- Compare local contracts and shared mechanisms only after the conceptual structure
  is established. The current-dev comparison is relevant but its temporary client
  lifetime cannot silently replace the pool's persistent-client contract.
- Full test31 and raw validation logs are indexed; relevant lifecycle/observer and
  fixture bodies were read. No claim that every unrelated test body was loaded.
- E1 and actual cross-account Telegram behavior remain a declared later boundary.

No in-scope frontier requires another Surfacing pass before Sensemaking; behavioral
re-testing is the next discipline's work. Unknown relevance was not filtered.

**Workspace-populated:** true; populated-at:2026-10-12T16:49:09.818565+00:00;
extent:31 recorded items/regions at named resolution. No candidate-generation
or stable causal model was inserted into this thin artifact.

## Telemetry and self-assessment

Artifact/signal-first; boundary-discovery:no; traversal cycles:5 (history, plans,
runtime, qualification, current-dev comparison). Entries31; core24/sub7/side0/
umbrella0; filesystem mtimes27/none4. Three convergence checks pass: bounded region
coverage, uncertainty-inclusive tagging, rejection only outside the high-confidence
scope. No silent sampling or workspace-overload truncation; selective test depth is
explicit. LAYER1 checked: Missed-relevance, Surfaced-irrelevance, Over-coverage,
Territory-mis-binding, Workspace overload, Artifact under-specification,
Workspace-artifact desync, Recency-Equates-Idleness, Recency-Bias-Filter. No flags.
LAYER2 safeguards: no interpretation, purpose loss or downstream-only calibration.

Repository structural_check.sh remains unavailable. Manual structural checks:
Reception; complete per-item trace metadata; coverage map; confirmed-absent limits;
concept provenance; recency aggregation; frontier; workspace status; telemetry;
no item-content reproduction — **10/10 PASS**. **Verdict: PROCEED.**
