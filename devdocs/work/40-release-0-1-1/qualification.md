---
model: gpt-6-astra
effort: xhigh
---
# Complete0.1.1 qualification — PASS

Candidate: git archive of main05904d12d3960b5af837d83fb177cc7f9b557b8a with exactly three substitutions: version0.1→0.1.1 in package __init__ and two existing export-test expected versions. Every98 Python source matches frozen main with only those transformations;95 files unchanged. No runtime feature behavior was changed.

**914 executed offline checks /31 suites /7 demos PASS;3 explicit live skips excluded.** All98 sources compile/pass Python3.7 grammar on Python3.11.10 / Telethon1.45.0; no native3.7 claim. Source hashes stayed unchanged through tests and package builds.

Real wheel and sdist each contain all90 expected Python package files including40 runtime modules, byte-for-byte matching the candidate. Name/version0.1.1, Python floor>=3.7, Telethon>=1.45,<2.0, pandas>=1.0, proxy extra and worker entry point match. README/setup source and metadata content match. No session/env/work/Duncan payload is present. Exact local archive hashes and metadata are in evidence/local-artifacts.json; independent CI archives may differ at container metadata, so later publication compares package contents plus PyPI-advertised hashes, not local whole-archive equality.

The actual local wheel installs with no dependencies/network into a new target. A Python isolated-mode probe resolves tgdata from that target, verifies0.1.1 distribution/runtime versions, all102 public exports, seven heartbeat=None signatures, opt-in trails and installed tgdata-worker --help. No live user or consumer environment was modified.

## Build setup corrections

The prior release's build-tool environment lacked wheel for a no-isolation build. That attempt stopped before producing a qualified artifact. A dedicated new temporary build environment was created; its venv initially seeded setuptools65.5.0, which generated legacy sdist PKG-INFO without Requires-Dist. The strict metadata check rejected it. Updating setuptools only in that temporary environment to84.0.0 (the fresh backend style used by CI) produced the required metadata. The checker and expected dependency/source conditions were unchanged. build1.6.1/wheel0.48.0/packaging26.3 are recorded. Initial missing-wheel output, initial tool versions and metadata failure are retained; these are tool setup corrections, not a package-source/architecture substitution or weakened feature assertion.

Full source verification passed before and independently of the packaging setup corrections; no source bytes changed during them. No adoption, merge, tag or upload occurred before this PASS. Next: formal fold, adopt exactly the three edits, review transport into dev/main, then actual pinned-main publication/read-back.
