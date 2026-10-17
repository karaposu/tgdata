Fixes `tgdata-login` refusing otherwise supported macOS terminals when the native `PENDIN` flag is set (#55, PR #56).

- Accepts pending-input state while preserving the existing hidden-input, authentication, session-save and cleanup safeguards.
- Corrects the previous refusal test and expands native terminal coverage, including plain and 2FA login, queued input, oversized input, interruption and unsupported flags.
- No dependency or public API change.

Qualification uses Python 3.11.10 and Telethon 1.45.0 on the available Darwin host. Native terminal checks use controlled Telegram transport without live account access. Three optional live checks remain skipped; other hosts are not newly certified.

Install: `python -m pip install --upgrade tgdata==0.1.3`
