# Brief — the account check before building #67 (critic.md: REORDER)

**What this is.** tgdata is adding an option to reach Telegram through its WebSocket endpoint by hostname. A no-account probe already showed that the transport works. What is still unknown is whether Telegram serves **this account's existing session** over that endpoint. That premise is what every build step depends on, so it is checked first, before any code is written.

**Run it only after the maintainer says go.**

## Safety — read first

- **Nothing else may use this account's session while the check runs.** Telegram revokes a session key that is used from two addresses at the same time. The account would be logged out and need a new login code.
  - Stop the account's normal application, and anything else that uses this session file, on every machine.
  - Then pass `--exclusive-confirmed`. The script refuses to run without it.
- **The script works on a copy of the session file.** The original is never written, and the copy is deleted at the end.
- **It never logs in, and never asks Telegram for a login code.** A session that is not logged in stops the run.
- **Downloads go to memory only.** Nothing else is written.
- **It takes about 7 minutes,** including 5.5 minutes of deliberate idle time.

## Setup

1. Python 3.11, in a fresh virtualenv:
   ```bash
   pip install telethon==1.45.0
   ```
   Also run `pip install 'python-socks[asyncio]'`, if the account's proxy is `socks5://` or `socks4://`.
2. Download the script from the public branch:
   ```bash
   curl -fsSLo experiment_account_check.py https://raw.githubusercontent.com/karaposu/tgdata/feat/67-websocket-hostname-transport/devdocs/work/67-websocket-hostname-transport/experiment_account_check.py
   ```
3. Have the account's tgdata config file ready. Its `[Telegram]` section holds `api_id`, `api_hash`, `session_file`, `proxy` and any pinned device fields, and the proxy must be the one that routes hostnames and refuses IP targets.

## Run

```bash
python experiment_account_check.py --config /path/to/account.ini --exclusive-confirmed
```

- **Step 4 needs a media file that Telegram stores on a different data centre from the account's own.** The script searches the account's channels for one. If it reports `SKIPPED`, rerun it with a large public channel the account can read:
  ```bash
  python experiment_account_check.py --config /path/to/account.ini --chat <channel_username> --exclusive-confirmed
  ```
- **Afterwards, restart the account's normal application and confirm it works.** That is the control: it shows the session is fine over the ordinary connection.

## Reading the result

The last block prints one of these:

| Result | Meaning |
|---|---|
| `PASS` | Every step worked over the WebSocket endpoint, by hostname: connect, `GetState`, `get_me`, a read, the other-DC download, and a read after the idle. The build goes ahead. |
| `DISQUALIFYING` | Telegram refused the account or its session over the endpoint. If the normal application works right afterwards, the refusal is specific to the WebSocket endpoint, and the feature's premise is false for this account. |
| `INCONCLUSIVE` | A step failed for a reason that is not an account refusal, such as a channel name typo or a network drop. Send the output back. |
| `INVALID RUN` | Another client was using the session (`AUTH_KEY_DUPLICATED`). The session may now be revoked; log the account in again before retrying. |
| `FAIL` | A connection named an IP address. This should never happen. Send the output back. |

Under "Connections Telethon opened", every line must be ✓ — a `*.web.telegram.org` hostname, never an IP address.

## Send back, privately

Don't post any of this anywhere public.

- the full terminal output;
- the date and time;
- whether the account's normal application worked when restarted afterwards.
