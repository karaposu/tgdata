---
model: gpt-6-astra
effort: xhigh
---
# Articulation — #45 history sampling

## User Input
```text
$task-impl |  |  |  |
|---|---|---|
| #45 — History sampling across days | P2 | Not started; next in our sequence |
```
Substrate: the full #45 issue and current same-session library/consumer readings. This inquiry qualifies the contract before task-impl writes its description and plan; it does not replace the requested implementation.

## Stage 1 — Itemize
Count:1. I1: implement #45, history sampling across days. Acquisition, selection and evidence are coupled aspects of this one feature, not independently requested projects.

## Stage 2 — MQ and alignment, I1
**MQ1 — What is the user asking for?** Explicit-empty: implementation through the named task-impl workflow is clear. The inquiry's required contribution is contract qualification, not an unsolicited alternative project.

**MQ2 — What context is needed?** Identified-ambiguities-list:
- verdict: which existing source/capture/value contract supports content and coverage; what “spread across days” means under a source cap;
- kinds: raw-message versus observed-post units; per-window versus per-day acquisition; replayable captured input versus a query-only result;
- stance: deterministic reading material versus statistical inference; pure local eligibility versus callbacks coupled to a live source operation; offline evidence versus conditional live qualification.

**MQ3 — What endpoint should the feature provide?** Identified-ambiguities-list: one bounded live sample call versus capture plus local reselection; equal-day versus traffic-weighted allocation; even rank versus deterministic randomized selection; complete-period capture versus bounded partial day observations; raw messages versus assembled albums/posts; synchronous caller predicate versus caller-supplied eligibility decisions.

**MQ4 — What is excluded?** Explicit-empty at exclusion ambiguity: the issue explicitly excludes embedded classifications/scoring/LLMs, scheduling, distributed workers, a new backfill lifecycle and unsupported population-representativeness claims. Existing batch identities/cursors/acknowledgments must remain compatible; omitted messages cannot imply progress. The implementation request does not authorize a merge or release.

**MQA — reconcile:** MQ2 kinds and MQ3 share the capture/selection-unit axis; preserve it jointly. MQ2 stance and MQ3 share caller-eligibility execution placement; preserve it jointly. WHY motivations below remain separate from these action endpoints. No forced resolution.

## Stage 3 — Deconstruct and MultiDepth, I1
Deconstruct tuple: (deliverable: qualified native sampling feature; kinds: contract findings followed by code/tests/public documentation and workflow records; bounds: fixed-period bounded content selection with traceable identities/coverage, preserving current readers and progress). No late item split indicated.
Literal statement: “Implement #45 — History sampling across days.” No added architecture is implied by this restatement.
WHY identified-ambiguities-list: improve human/LLM reading usefulness; avoid newest-only bias; control Telegram and downstream reading costs; make repeated analysis auditable; reduce duplicate application code. These motivations can coexist but imply different priorities between acquisition breadth, retained input and selected output size.

## Stage 4 — considered articulations, I1
1. Implement a bounded source sampler that explicitly distributes reading and selected raw messages across UTC days, returning selection and incomplete-day evidence.
2. Implement a bounded content capture plus reproducible local selection, allowing the same captured input and caller eligibility to be reselected without Telegram.
3. Implement sampling over observed assembled posts/albums, explicitly preserving original members and distinguishing observed membership from source completeness.
4. Build on existing immutable MessageBatch capture with a pure temporal selection helper and a native bounded source wrapper, preserving the current batch schema and progress semantics.
All variants preserve the requested feature deliverable, span identified dimensions, respect exclusions and use concepts present in the loaded substrate. None is selected.

## Self-assessment
Nine LAYER1 modes: no fire for premature split, late multi-item signal, MQ extension, missing operation, missing preparation axes, missing kinds/stance, 2-shape violation, WHAT/WHY conflation or composition drift. Lightweight single pass; no separate verification machinery. Bundle and four-stage structure complete; four variants, one item, no flags. **HIGH-PROCEED**.
