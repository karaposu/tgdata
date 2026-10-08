---
model: gpt-6-astra
effort: max
---
# PR21 probe output

2026-10-08; product2fe9aeb, Telethon1.45.0/Python3.11.10. Exit0.
All eight emitted observation records, formatted for readability:

```json
[
  {
    "probe": "delayed_resolution",
    "observed": {
      "actual": 333,
      "claims": 0,
      "history_sends": 0,
      "closed": true
    }
  },
  {
    "probe": "cancel_admission",
    "observed": {
      "cancelled": true,
      "claims": 0,
      "history_sends": 0,
      "close_attempts": 1
    }
  },
  {
    "probe": "reversed_initial_proofs",
    "observed": {
      "opened": [
        222,
        333
      ],
      "verified_order": [
        333,
        222
      ],
      "owners_correct": true,
      "closed_clients": 2
    }
  },
  {
    "probe": "session_close_failures",
    "observed": {
      "preserved": [
        [
          "OSError",
          "success"
        ],
        [
          "OSError",
          "primary error"
        ],
        [
          "CancelledError",
          "success"
        ],
        [
          "CancelledError",
          "primary error"
        ]
      ],
      "sanitized_error_logs": 4,
      "sdk_background_tasks_finished": true
    }
  },
  {
    "probe": "cancel_over_primary_and_failed_close",
    "observed": {
      "outcome": "CancelledError",
      "close_attempts": 1,
      "detached_close": false
    }
  },
  {
    "probe": "preconstruction_failures",
    "observed": {
      "store_load": "OSError",
      "corrupt_snapshot": "ValueError",
      "proxy": "ProxyConfigError",
      "built_clients": 0
    }
  },
  {
    "probe": "successful_iterator",
    "observed": {
      "message_ids": [
        101
      ],
      "billed_account": 222,
      "billed": 1,
      "cached_account": 111
    }
  },
  {
    "probe": "bootstrap_self_shapes",
    "observed": [
      {
        "reply": "None",
        "exception": "TypeError",
        "body_entered": false,
        "closed": true
      },
      {
        "reply": "empty list",
        "exception": "IndexError",
        "body_entered": false,
        "closed": true
      },
      {
        "reply": "UserEmpty",
        "exception": "AttributeError",
        "body_entered": false,
        "closed": true
      }
    ]
  }
]
```

Other output: Telethon warned that the deliberately injected async session.close
uses experimental async-session support; the combined cancellation/cleanup-failure
probe logged `Account operation cleanup failed (OSError)`. Neither message included
the synthetic credential marker. No socket connections were permitted.
