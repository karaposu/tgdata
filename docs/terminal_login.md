# Terminal account login

Use the installed `tgdata-login` command to log in deliberately and save a native
Telethon SQLite session for ordinary tgdata readers. It uses the existing
[LoginFlow API](stepwise_login.md), including the configured proxy and device
settings. It does not change background readers' refusal to prompt for login.

## First login

Create the ordinary reader's configuration with your API credentials and session
destination. The destination's parent directory must already exist.

```ini
[Telegram]
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
session_file = /absolute/path/to/account-primary
# Optional proxy/device settings are the same as for the reader.
```

Run in an interactive terminal:

```bash
tgdata-login --config config.ini
# Equivalent module invocation:
python -m tgdata.login_cli --config config.ini
```

The command shows the absolute destination before requesting a code. Supply the
phone number with country code, then the code Telegram delivers, and the 2FA
password if requested. All three inputs are hidden. Input refuses if echo cannot
be disabled. No secret input, credential or checkpoint option is accepted on the
command line. Unknown-argument diagnostics do not repeat the supplied values.

Success reports the authenticated numeric account ID and destination after the
file is published and its parent directory is synced. It never prints the session
credential. A native SQLite reader can use the result directly:

```python
from tgdata import TgData

tg = TgData("config.ini", interactive_login=False)
# Use the usual reader APIs, then await tg.close().
```

The output is a SQLite `.session` file, not the opaque string returned by
`LoginFlow.session_data`. The command performs that conversion privately using
the existing codec and native session APIs. It preserves the authorization key,
data centre, own-account ID marker, available own-account cache row and update
states. Optional absence of an access hash does not make a completed login invalid.

## Entering values

Every prompt, including confirmations, accepts at most **128 UTF-8 bytes**. This is
128 ASCII characters, or fewer characters when their encoding uses several bytes.
Supply one value at a time after its prompt: input queued before a prompt and extra
lines already queued after an answer are discarded.

The command requires a foreground interactive POSIX terminal in its ordinary
canonical, 8-bit input mode, with Ctrl-C configured as interrupt. Unsupported modes
or control bindings are refused before login starts and checked again at each
prompt. Run it directly from the terminal's main thread, outside an existing
Python event loop.

Input is hidden, including `REPLACE` and save-retry answers. The terminal's
configured erase key removes one Unicode scalar, which can be only part of a
combined visible character; its clear-line key clears the current value. Enter
finishes the value. The configured EOF key (usually Ctrl-D) stops the command,
including when a partial value has been typed. Ctrl-C requests a stop.

Cursor keys, history, literal-next, software flow controls, quit and suspend keys
are not supported for entering a value. An oversized line or unsupported input
control is rejected and remains rejected: erase or clear cannot make its remaining
suffix into an answer. The command keeps the line hidden and discards it until
Enter, EOF or Ctrl-C. There is no overall timeout while waiting for your input.
Malformed UTF-8 also refuses the value; input is never silently shortened or
normalized. A local input refusal ends this command, so restart it deliberately.

A value reaches login or saving only after terminal settings are restored. If
restoration or resource cleanup fails, the command reports that failure and releases
no value. It cannot guarantee repair after an operating-system failure or control
input written after it has exited. Use the [LoginFlow API](stepwise_login.md) for
applications needing different input handling or longer values.

## Destination rules

`--config` defaults to `config.ini`. Session naming matches the reader: an explicit
`session_file` wins, then the legacy `username` setting, then `telegram_session`.
The `.session` suffix is appended if absent.

Relative session names are relative to the invoking working directory, not the
configuration file's directory. A literal `~` is not expanded differently from
the reader. Prefer an absolute path. The command does not edit your configuration.
Displayed paths escape control characters.

The initial command supports trusted local POSIX filesystems with the required
link, atomic replacement and directory-sync operations. It refuses unsupported
platform/capability or an unwritable destination parent before requesting a code.
These checks do not establish guarantees for network filesystems, hostile directory
writers, storage devices that misreport synchronization, or every power-loss case.

## Deliberate re-login

By default, an existing destination is refused before authentication. To replace
it deliberately:

```bash
tgdata-login --config config.ini --replace
```

After authentication, the command shows the account ID and destination and asks
you to type `REPLACE`, confirming both the intended replacement and that **all
readers using this session are stopped**. Keep them stopped until publication or
recovery is resolved. There is no automatic confirmation option.

The command rejects a destination symlink, nonregular file, SQLite `-wal`, `-shm`
or `-journal` sidecar, or a destination that changed during the conversation. It
does not delete sidecars to force progress. Close the owning readers and resolve
their SQLite state before trying again. A missing sidecar is not proof that all
readers have stopped; this remains the operator's responsibility.

An initially absent destination always uses no-clobber creation, even with
`--replace`. If another file appears while you enter the code, it is preserved
and publication refuses. Replacement authorization is not silently refreshed to
cover a different file.

## Authentication and saving are separate outcomes

The command prepares a closed, locally verified SQLite candidate in a private
directory beside the destination. That directory has mode0700; the new session
file has mode0600. It never opens or upgrades the old database during login.

For replacement, the old file is linked into that private directory before the
switch. The command syncs the directory's parent, the old file's bytes and the
backup link before attempting replacement. After publication it syncs the
destination parent. Successful cleanup removes the temporary candidate/backup.

- A failure before destination mutation leaves the old destination unchanged.
  For a recoverable local I/O failure, the command offers a save retry using the
  completed credential already in memory. No new code or sign-in request is sent.
- If publication may have happened but its result or persistence cannot be
  established, the command reports **publication uncertain** and retains private
  recovery files. It does not blindly retry, roll back or claim nothing was saved.
- A cleanup failure after confirmed publication leaves the outcome **saved**.
  The command reports the retained private directory for manual cleanup.
- A broken output stream cannot reverse a known successful publication. If the
  command was interrupted after saving, it reports the saved outcome when output
  is available and exits as interrupted.

Treat any reported recovery directory as credential-bearing material. Keep
readers stopped, inspect which native session is at the destination, and use the
retained `previous.session` when recovering the old credential is appropriate.
Do not delete recovery material until the intended state is established. No
automated recovery command or permanent credential archive is provided.

Filesystem calls are synchronous. Ctrl-C is deferred during the local publication
section long enough to record its effect. A pending stop noticed before mutation
prevents publication; one arriving after publication does not undo the saved
file. This is not a guarantee of bounded filesystem latency or recovery from
SIGKILL, machine failure or arbitrary concurrent writers.

## Invalid input, waits and interruption

Phone/code/password values rejected by the login API can be corrected at the same
eligible step. Local terminal framing or cleanup failures instead end the command.
The command does not resend codes automatically. Waits report the remaining delay
and stop. Expired/restart-required, unsupported and additional password-setup
responses stop explicitly rather than being silently treated as a saved login.

After an uncertain source reply, the command offers one explicit authorization
check that sends no code. It may discover the completed login or return to an
eligible input step. It never replays the previous code/password automatically.

EOF and Ctrl-C request a stop for the whole command. At an input prompt, Ctrl-C
records the stop while the input owner discards pending input and restores the
terminal settings; another Ctrl-C does not interrupt that restoration. During authentication, it requests cancellation of the
active action once and waits for its owned cleanup. Native password computation
may need to finish before cancellation is observed. Repeated Ctrl-C does not skip
cleanup or start another cancellation of the cleanup itself.

An in-flight authentication request may already have reached Telegram before the
stop is observed. The command preserves known or uncertain authorization state,
but starts no next prompt, login action, authorization check or save after stopping.
There is no automatic recovery of that in-memory login conversation.

Cleanup remains eligible after a stop, and failed cleanup is reported safely.
The exit code is chosen after finalization, so a late Ctrl-C still yields130 while
an already saved or uncertain session keeps its reported publication outcome.
There is no bounded computation, filesystem or disconnect timeout. No socket is
held while waiting for the next input after a settled step.

| Exit | Meaning |
|---|---|
| 0 | Session publication is confirmed. Cleanup/output warnings do not undo it. |
| 2 | Usage, configuration, terminal or destination preflight refusal; no login started. |
| 3 | Login stopped: wait, unsupported/restart state, source failure, local input failure or unsettled cleanup. |
| 4 | Local preparation/save or its confirmation input failed without publication, or a target conflict refused. |
| 5 | Publication outcome is uncertain; inspect destination and retained recovery files. |
| 130 | Operator interrupted, supplied EOF or declined replacement. The reported publication state still matters: a file may already have been saved, or publication may be uncertain. |

The command retains save-retry state only in memory. It does not write LoginFlow
checkpoints or automatically resume a killed process. Applications needing custom
stores or explicit checkpoint ownership should use the existing
[step-by-step API](stepwise_login.md).

## Validation limits

Offline tests combine actual Telethon1.45.0/LoginFlow/SRP/session codecs, native
SQLite files, an ordinary configured reader and real PTY/signals with controlled
Telegram replies. Sockets are forbidden. These tests do not qualify live code
delivery or real-account password acceptance. Live use needs the operator's own
authorized account setup; filing or testing this feature never initiates it.
