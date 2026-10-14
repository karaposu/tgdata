# Local verification correction — exact lookup comparisons

The56-case candidate and full829-check suite passed. An additional actual SQLite compatibility probe then constructed tables whose column declarations used NOCASE while their primary/post indexes used BINARY and otherwise matched the validated schema. With only collection `Tenant` registered, opening `tenant` succeeded and its duplicate accept confirmed `Tenant`'s input. Observed output:

```
REPRODUCED: nonexistent lowercase collection confirmed uppercase collection input
Receipt collections: [('Tenant',)]
```

This was a local call-site omission of the plan's existing byte-exact identity rule: WHERE predicates inherited column collation. The correction explicitly selects COLLATE BINARY for collection, post and batch lookups, matching their validated indexes. It changes no data format, admission/confirmation contract, receipt ownership or plan step. It is permitted by task-impl's local nonarchitectural verification-correction rule.

The new permanent test `test_collection_lookup_uses_exact_keys_not_column_collation` builds that actual schema, requires the nonexistent lowercase collection to refuse, explicitly creates it, then verifies separate records/markers and successful zero-write confirmations for both collections. It passed in the corrected full57-case candidate; all13 related suites and the demo also passed before adoption. The original56-case candidate/result and initial full-verification manifest are retained as evidence.

No source engine, public album core or existing test expectation was changed. This correction is explicitly reported rather than silently counted as a clean first implementation run.
