# Brief — the live check of the built #67 transport (plan step 14)

**What this is.** tgdata now has `transport = websocket`. This check runs **tgdata's own built code** on the real account, through the account's proxy, to confirm success criterion 14:
- login with the existing session;
- reads;
- a download from another data centre;
- surviving the connection cuts by reconnecting by name.

A prototype of the same check already passed before the build (`experiment_account_check.md`). This run confirms that the built code behaves the same way.

**Run it only after the maintainer says go.**

## Safety — read first

- **Nothing else may use this account's session while the check runs.** Telegram revokes a session key that is used from two addresses at the same time (`AUTH_KEY_DUPLICATED`). The account would be logged out and need a new login code.
  - Stop every application that uses this session file, on every machine.
  - Then pass `--exclusive-confirmed`. The script refuses to run without it.
- **The script copies the config and the session file into a temp folder,** uses the copies, and deletes them at the end. The originals are never written.
- **It never logs in, and never asks Telegram for a login code** (`interactive_login=False`).
- **Downloads go to memory only.**
- **It takes about 7 minutes,** including 5.5 minutes of deliberate idle time.

## Setup

1. Python 3.11, in a fresh virtualenv. Install tgdata from the feature branch with the proxy extra; `python-socks` is needed for every proxy kind, `http://` included:
   ```bash
   pip install "tgdata[proxy] @ git+https://github.com/karaposu/tgdata@feat/67-websocket-hostname-transport"
   ```
   This pulls in Telethon 1.45.0.
2. Download the script:
   ```bash
   curl -fsSLo live_check.py https://raw.githubusercontent.com/karaposu/tgdata/feat/67-websocket-hostname-transport/devdocs/work/67-websocket-hostname-transport/live_check.py
   ```
3. Prepare the account's tgdata config. Its `[Telegram]` section needs:
   - `api_id`, `api_hash` and an explicit `session_file`;
   - the hostname-routing `proxy`;
   - any pinned device fields;
   - **`transport = websocket`**.

## Run

```bash
python live_check.py --config /path/to/account.ini --chat <a large public channel> --exclusive-confirmed
```

The channel must be one the account can read, with media stored on a data centre other than the account's own. A large public channel usually qualifies.

## Reading the result

| Result | Meaning |
|---|---|
| `PASS` | All of these worked through tgdata: connect, a read, the other-DC download, a read after the idle, and `health_check()` reporting `transport='websocket'`. |
| `REFUSED` | Telegram refused the account or its session. |
| `INCONCLUSIVE` | A step failed for another reason, such as a channel typo or a network failure. Send the output back. |
| `INVALID RUN` | Another client was using the session (`AUTH_KEY_DUPLICATED`). |
| `FAIL` | A connection named an IP address. This should never happen. |

**Under "Connections Telethon opened":**
- every line must be ✓, a `*.web.telegram.org` hostname;
- one or more **reconnects** are expected: the door or the proxy cuts connections every few minutes, and tgdata's ordinary client reconnects by name.

## Send back, privately

Don't post any of this anywhere public: the output may include the proxy's exit address.

- the full terminal output;
- the date and time.
