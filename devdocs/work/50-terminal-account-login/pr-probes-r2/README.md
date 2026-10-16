# Renewed PR51 review probes

Exact product root:/private/tmp/tgdata-50-terminal-login-pr, head34907d4.
Python3.11.10/Telethon1.45.0; actual SDK/session/files/PTY/getpass/termios with
controlled source transport. All socket connect/connect_ex calls are forbidden.
No product file or permanent test was changed.

input_restore_probe.py uses actual hidden input in an owned PTY. At getpass's native
restore call, a wrapper sends a real process SIGINT before calling the original
termios.tcsetattr. This exposes a valid first-signal interleaving in the restoration
finally, without changing the CLI or supplying a fake terminal result. Three cases:

- Enter normally, then first SIGINT at restoration: exit130, echo stays disabled.
- EOF, then first SIGINT at restoration: exit130, echo stays disabled.
- Ctrl-C while reading, then another SIGINT at restoration: exit130, original
  terminal settings restored. This is the control covered by the permanent suite.

The probe observes termios state after the command returns, then explicitly restores
its own child terminal for cleanup. No login-code request or file publication occurs
in any case. input-restore-result.json records all three outcomes. A caller/shell
may repair terminal settings independently; the command itself did not in the first
two histories. No secret echo or credential loss is demonstrated.

crossings.py adds13 passing actual-component histories: invalid input plus stop;
wait/error plus stop; authorization-only recovery success/error plus stop; known
auth with failed close plus stop; backup bytes/directory failure plus stop; stop
while answering a save retry; uncertain publication followed by a shutdown stop;
two local save retries without another auth request; and real pending-task/async-
generator retirement with repeated signals after confirmed publication. It checks
actual old/new bytes, source counts, closed wires, saved/uncertain state and source
hashes. crossings.txt and crossings-result.json retain observations/manifests.

native_srp_regression.py reruns the original actual-native-SRP/PTY falsifier on the
new head. Only its expected outcome was changed to the revision4 contract: child
returns130, no saved session, no timeout kill. Native computation remains real and
the signal-active marker is asserted. It passes, confirming that the old hang was
fixed rather than relabelled. pty-native-srp-result.json retains the transcript.

There were no probe fixture corrections, product changes or acceptance weakening.
The new defect is a different phase: a FIRST signal during restoration after a
normal return/EOF, not a repeated signal after the owner has already recorded a
read-time interruption. Installed Python getpass.py:75–80 and CLI prompt/_signal
explain the precise mechanism. Previous full-suite/prebuild records remain intact;
these fresh histories supplement them, not a claimed live Telegram qualification.
