# Decomposition — terminal login publication
## User Input
`_branch.md`, using saved sensemaking SV6: separate remote authentication from compatible local publication while preserving all four candidate scopes.

## 1. Coupling map
Strong clusters:
- Configured destination interpretation, old-file/sidecar checks, replacement intent, candidate visibility, backup/retention, durability outcome and cleanup are one publication lifetime. Splitting preflight from publication into unrelated owners would lose the before/after comparison.
- Terminal input, LoginFlow step/status, explicit retries, Ctrl-C/EOF and credential-safe reporting form one operator conversation. Retained complete credentials must remain reachable for a local save retry.
- StoredSession decoding, native SQLite construction, own-identity state and read-back verification form a representation bridge.
- Installed entry point, docs and real composition tests share the externally visible contract, not live mutable credentials.

Moderate crossings: conversation hands a settled secret credential/account to conversion; conversion hands a closed candidate and identity evidence to publication; publication returns a safe outcome to the conversation.
Weak crossing: packaging calls command main. Existing reader behavior is a consumer contract and test oracle, not a new mutable dependency.
No crossing: sampler/backfill/pool scheduling, production ScrapeOps deployment or a distributed coordinator.

## 2. Top-down boundaries
Q1 publication lifetime contains preflight plus final decision; Q2 operator/auth conversation consumes existing LoginFlow; Q3 native representation bridge consumes only settled complete credentials; Q4 delivery/verification binds the three into an installed command. No standalone “ask phone” or “write one column” pieces.

## 3. Bottom-up validation
Atoms: a source request and its retained LoginFlow state cannot be separated; replacement compare/publish/outcome cannot be split around unrelated error owners; native SQLite commit/close and candidate verification belong together; a safe prompt/output belongs with its input interpretation.
All atoms fit the four boundaries. Q1 contains subquestions for preflight, visibility and persistence but one owner; this preserves strong timing coupling. High confidence on all four boundaries. Stop at tractable questions rather than fragmenting lifecycle into one function per state.

## 4. Question tree
### Q1 — What target may be changed, and when is that change known?
- Define exact configured path and backend, create-versus-replace intent, reader quiescence and trusted-directory preconditions.
- Determine applicability at runtime: nonsymlink regular destination or absence; sidecars, destination change during human input and filesystem capabilities.
- Define candidate publication point, old-state preservation, cleanup and safe outcomes before/after an uncertain syscall.
- Verify by actual filesystem fault injection, collision/changed destination and reader reopen; no new auth calls on retries.
- Q1a target assessment; Q1b publication/durability/old retention; Q1c outcome evidence. These remain within one owner.

### Q2 — How does a terminal user drive the existing flow without changing its rules?
- Prompt only at eligible steps; secret inputs do not echo or enter logs/argv.
- Respect wait/restart/unsupported/uncertain/cleanup states; explicit retries cannot silently resend.
- Keep completed credentials while retrying local save; define EOF/Ctrl-C behavior at input, source and publication boundaries.
- Consume Q1's safe outcomes rather than infer publication from an exception type.
- Verify with real LoginFlow plus controlled Telegram source and terminal interruption probes.

### Q3 — What makes a completed credential usable by the existing file reader?
- Consume a complete settled credential plus authenticated numeric account.
- Decode through StoredSession and create SQLite with native SDK APIs; no hand-written auth/schema interpretation in the UI.
- State which auth/DC/own-row/update data is preserved and verify the candidate after close.
- Ensure candidate bytes stay private and destination remains untouched until Q1 publishes.
- Verify actual ordinary reader authorization from the candidate/published file without login prompts.

### Q4 — How is the completed contract delivered and proven?
- Installed entry point and module invocation share one command path; configuration/name semantics match readers.
- Public docs distinguish auth completion, local publication, uncertainty and live-validation limits.
- Permanent integration tests cover Q1–Q3 together, including failed save and original error/cleanup precedence; relevant/full existing suites remain passing.
- Verify isolated installation/help/refusal behavior without real credentials or network.

## 5. Interfaces, including assumptions
| From → to | Flow | Assumption to make explicit |
|---|---|---|
| Config/operator → Q1 | destination and replacement intent | same config/name resolution as reader; readers stopped throughout sensitive publication |
| Q1 → Q2 | preflight acceptance or safe refusal | no destination creation/truncation during unfinished authentication; acceptance is not a lease |
| Q2 → Q3 | secret settled credential and observed account ID | complete status and cleanup settled; no API call concealed in conversion |
| Q3 → Q1 | closed private native candidate plus expected identity | schema/key/DC/own rows verified; same filesystem for selected publication primitive |
| Q1 → Q2 | safe publication outcome and retained recovery paths if any | failure means untouched only if established; uncertainty never invokes a new code request |
| Q2 → Q1 | explicit save retry/stop | retry uses retained completed candidate; does not broaden old-destination authorization |
| Q1/Q2/Q3 → Q4 | stable interfaces and evidence | tests must exercise actual SDK/storage/terminal seams, not supply desired outcomes |
| Published file → existing reader | native SQLite session | file format and configured path match; no runtime code migration or extra login required |

No public secret token or shared background task crosses these boundaries. A custom-store variant must provide the same publication-outcome contract; lack of a concrete adapter is not hidden behind an abstract save callable.

## 6. Dependency order
First settle Q1/Q2's success/refusal/uncertainty interface and supported destination scope.
Then prove Q3's representation and Q1's filesystem primitives locally before dependent implementation.
Compose Q2 with Q1/Q3, then Q4 installs and verifies the actual command. Q1 and Q3 can be investigated independently once the closed-candidate contract exists, but this inquiry remains sequential. There is no circular implementation dependency; the retry loop passes decisions/outcomes, not shared implementation ownership.

## 7. Reassembly and self-evaluation
Reassembly: an explicit command identifies the permitted destination; a human supplies inputs through LoginFlow; the completed secret becomes a verified native candidate; publication returns a truthful outcome; normal readers reopen it; failures remain actionable without remote replay.
Determination mechanisms are assigned to Q1 (target/type/sidecars/change/capability), Q2 (flow phase/TTY/cleanup) and Q3 (credential/reader compatibility); no “safe destination” predicate is left magical.

Seven dimensions: independence PASS through interfaces; completeness PASS across all success/failure/format/entrypoint surfaces; reassembly PASS; tractability PASS with Q1's three subquestions; interface clarity PASS including assumptions; balance PASS (publication intentionally largest, decomposed internally); confidence PASS (top-down/bottom-up agree).
Four variants still fit: native replace, concrete store, create-only and checkpoint recovery differ in Q1/Q2 policy, not in bypassing Q3/Q4 proof. No destination policy selected by this partition.

Telemetry:4 pieces,3 Q1 subquestions,8 interface flows,7/7 self-evaluation. Seven failure modes checked; no premature split/hidden state/omitted applicability check detected. Manual structure7/7 (input/coupling/top-down/bottom-up/questions/interfaces/order+self-evaluation); checker absent. Ready for Innovation.
