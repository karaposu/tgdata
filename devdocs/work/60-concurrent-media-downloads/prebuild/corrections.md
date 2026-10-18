# Candidate preparation corrections

The first25 native concurrency groups passed. The complete35-group run then found:

1. SDK-owned normal iterator.close was called inside _load_next_chunk, before the
   outer resource finalizer. Its injected cleanup RPC-shaped error escaped as a source
   error. The planned cleanup isolation existed only at our finalizer call site.
   Local correction: wrap the tracked iterator's close itself with the same retained
   settlement/local-error rule, covering both SDK and owner call sites. This adds no
   new ownership, retry or result design; step1 already requires all cleanup errors
   to remain local and preserve caller cancellation. Original assertion stays.
2. The legacy reuse fixture used application/octet-stream. Telethon.get_extension
   returns an empty extension, and the existing legacy cache deliberately only skips
   a download when extension is nonempty. Correct the reuse fixture to image/jpeg,
   the supported existing-cache case. Keep the assertion of zero additional downloads.
   No production caching behavior or expected result is relaxed.

First outputs preserved. Neither correction changes the six-step contract. Required
failed cases rerun before complete candidate qualification. No product adopted.

3. An added real-SDK queued-stop probe observed a second history request after the
   heartbeat callback called current_task().cancel(). A cancellation checkpoint existed
   before worker-window starts but was missing at the source-admission call site. Add
   one await-sleep-zero checkpoint before gate admission. This enforces the existing
   planned stop-before-new-source-work rule; no retry/ownership/interface design change.
   Keep the original assertion of one history request and rerun it, then the full suite.
