---
model: gpt-6-astra
effort: xhigh
---
# Surfacing — #37

## User Input
Implement the discussed batch heartbeat, without a new branch.

## Traversal Trace
The22 individually tagged items, timestamps and coverage records are in surfacing-trace.json. Four passes covered public forwarding, actual SDK progress/waits, storage/pool lifecycle and consumer/verification. This is artifact-mode, signal-first, explicitly bounded; no boundary-discovery was needed. Items were read into this continuing session; metadata never determined relevance.

## State Summary
PROCEED. Core: callbacks/reader/request seam; sub: source acknowledgment, budget and owned pool lifetime; umbrella: workflow. No persistent heartbeat model or new media format is required. All identified relevant regions are covered at the needed function/interface resolution, with unchanged full-source context retained. No unresolved frontier or absent-but-assumed SDK wait hook is claimed.
