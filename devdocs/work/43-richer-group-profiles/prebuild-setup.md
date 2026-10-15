---
model: gpt-6-astra
effort: xhigh
---
# Prebuild setup correction

The first attempt passed the four actual composition variants, then stopped
before the second probe's request because the fixture used MessageEmpty(8)
without the peer_id argument required by Telethon's custom Message constructor.
Observed error: TypeError: Message.__init__() missing 1 required positional
argument: 'peer_id'. The fixture now explicitly supplies peer_id=None, as the
existing group-access suite does. No runtime code, assertion, expected behavior
or experiment pass/fail condition changed. The complete experiment is rerun;
this setup error is not evidence that the SDK composition premise failed.
