"""Deliberate terminal login; authentication remains in LoginFlow."""

import argparse
import asyncio
import getpass
import signal
import sys
import threading
import warnings

from .login import LoginFlow, LoginError
from .login_file import LoginDestination, LoginFileError


class _Stopped(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # Unknown arguments may be a mistakenly supplied password/code.
        self.print_usage(sys.stderr)
        self.exit(2, 'tgdata-login: invalid arguments\n')


def _say(message):
    print(message, file=sys.stderr, flush=True)


def _safe_say(message):
    try:
        _say(message)
    except Exception:
        pass


def _hidden(prompt):
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        return getpass.getpass(prompt, stream=sys.stderr)


def _confirm(prompt, expected='yes'):
    return input(prompt).strip().lower() == expected.lower()


class _TerminalRun:
    """One command's stop intent, separate from an action's terminal outcome."""

    def __init__(self, loop):
        self.loop = loop
        self.stopped = False
        self._input = False
        self._active = None
        self._previous_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._signal)

    def _signal(self, signum, frame):
        self.stopped = True
        if self._input:
            # Only the first signal unwinds input. Further signals must not
            # interrupt getpass' terminal restoration in its finally block.
            self._input = False
            raise KeyboardInterrupt
        registration = self._active
        if registration is not None and not registration['retire']:
            self._request_cancel(registration)

    def _request_cancel(self, registration):
        if not registration['queued']:
            registration['queued'] = True
            self.loop.call_soon_threadsafe(self._cancel, registration)

    def _cancel(self, registration):
        # Check identity and delivery again in the loop: even reentrant signal
        # scheduling cannot cancel a later action or send a second cancellation.
        if (self._active is registration and not registration['retire']
                and not registration['sent'] and not registration['task'].done()):
            registration['sent'] = True
            registration['task'].cancel()

    def check(self):
        if self.stopped:
            raise _Stopped()

    def prompt(self, function, *args):
        self.check()
        self._input = True
        try:
            self.check()
            value = function(*args)
        finally:
            self._input = False
        self.check()
        return value

    def drive(self, factory, *, retire=False):
        if not retire:
            self.check()
        # Factory avoids creating an unawaited coroutine when stop already won.
        task = asyncio.ensure_future(factory(), loop=self.loop)
        registration = dict(task=task, retire=retire, queued=False, sent=False)
        self._active = registration
        try:
            if self.stopped and not retire:
                # Deliver a stop arriving during registration before source work.
                self._cancel(registration)
            while not task.done():
                try:
                    self.loop.run_until_complete(task)
                except KeyboardInterrupt:
                    # Defensive task-raised KI, not our async SIGINT policy.
                    self.stopped = True
                    if not retire:
                        self._cancel(registration)
                except BaseException:
                    if task.done():
                        break
                    raise
            try:
                result = task.result()
            except (KeyboardInterrupt, asyncio.CancelledError):
                self.stopped = True
                raise _Stopped() from None
            except BaseException:
                if self.stopped and not retire:
                    raise _Stopped() from None
                raise
            if not retire:
                self.check()
            return result
        finally:
            if self._active is registration:
                self._active = None

    def close(self):
        # No active registration survives into loop close or handler restoration.
        self._active = None
        self._input = False
        try:
            self.loop.close()
        finally:
            asyncio.set_event_loop(None)
            signal.signal(signal.SIGINT, self._previous_handler)


def _settle_flow(run, flow):
    if flow.status.cleanup_pending:
        run.drive(flow.close, retire=True)
    if flow.status.cleanup_pending:
        raise LoginError('cleanup_required')
    run.check()


def _login(run, flow):
    checked_uncertain = False
    while True:
        _settle_flow(run, flow)
        status = flow.status
        if status.action_required:
            _say('Login requires unsupported action: ' + status.action_required)
            return False
        if status.retry_after:
            _say('Login must wait {} seconds; no code resent.'.format(status.retry_after))
            return False
        if status.step == 'complete':
            return True
        if status.step in ('restart_required', 'unsupported'):
            _say('Login stopped: ' + status.step + '; no automatic restart.')
            return False
        if status.step == 'uncertain':
            if checked_uncertain or not run.prompt(_confirm,
                    'Login outcome uncertain. Check authorization without another code? Type yes: '):
                _say('Login outcome uncertain; session not published.')
                return False
            checked_uncertain = True
            try:
                run.drive(flow.check_authorization)
            except LoginError as error:
                _say('Authorization check: ' + error.kind)
                if flow.status.step != 'complete':
                    return False
            continue
        if status.step == 'phone':
            prompt, action = 'Phone number with country code (hidden): ', flow.start
        elif status.step == 'code':
            prompt, action = 'Telegram code (hidden): ', flow.submit_code
        elif status.step == 'password':
            prompt, action = 'Two-factor password (hidden): ', flow.submit_password
        else:
            _say('Unsupported login state; session not published.')
            return False
        value = run.prompt(_hidden, prompt)
        try:
            run.drive(lambda: action(value))
        except LoginError as error:
            _say('Login: ' + error.kind)
            if error.retry_after:
                _say('Retry after {} seconds; no code resent.'.format(error.retry_after))
            _settle_flow(run, flow)
            if flow.status.step in ('complete', 'uncertain'):
                continue
            if error.kind not in ('invalid_phone', 'invalid_code', 'invalid_password'):
                return False
        finally:
            value = action = None


def _publish(run, destination, credential, account_id):
    run.check()
    return destination.save(credential, account_id, stop_requested=lambda: run.stopped)


def _report(result):
    if result is None:
        return
    if result.status == 'published':
        _say('Saved session for account {} to {!r}.'.format(result.account_id, result.destination))
    elif result.status == 'publication_uncertain':
        _say('Session publication is uncertain ({}); inspect the destination before retrying.'
             .format(result.error_kind))
    elif result.error_kind:
        _say('Session not published ({}).'.format(result.error_kind))
    if result.recovery_directory:
        _say('Private recovery files: {!r}'.format(result.recovery_directory))
    if result.cleanup_warning:
        _say('Temporary-file cleanup failed; the publication outcome above is unchanged.')


def _safe_report(result):
    try:
        _report(result)
    except Exception:
        pass


def _effect_exit(destination, fallback):
    if destination is not None:
        if destination.outcome.status == 'published':
            return 0
        if destination.outcome.status == 'publication_uncertain':
            return 5
    return fallback


def _save(run, flow, destination):
    run.check()
    account_id = flow.status.account_id
    _say('Authenticated account {}.'.format(account_id))
    if destination.replacing and not run.prompt(_confirm,
            'Replace {!r} with account {} after stopping ALL readers? Type REPLACE: '
            .format(str(destination.path), account_id), 'replace'):
        _say('Replacement cancelled; previous session unchanged.')
        run.stopped = True
        return 130
    run.check()
    credential = flow.session_data
    while True:
        result = _publish(run, destination, credential, account_id)
        _report(result)
        if run.stopped or result.error_kind in ('interrupted', 'KeyboardInterrupt'):
            run.stopped = True
            return 130
        if result.status == 'published':
            return 0
        if result.status == 'publication_uncertain':
            return 5
        if not result.retryable or not run.prompt(_confirm,
                'Retry saving this completed login without another code? Type yes: '):
            return 4


def _retire(run, flow, destination):
    if flow is not None and flow.status.cleanup_pending:
        try:
            run.drive(flow.close, retire=True)
        except (Exception, KeyboardInterrupt, asyncio.CancelledError):
            _safe_say('Login cleanup remains incomplete; no further source work started.')
    if destination is not None:
        before = destination.outcome
        result = destination.close()
        if result.cleanup_warning and not before.cleanup_warning:
            _safe_report(result)
    pending = [task for task in asyncio.all_tasks(run.loop) if not task.done()]
    for task in pending:
        task.cancel()
    if pending:
        try:
            run.drive(lambda: asyncio.gather(*pending, return_exceptions=True), retire=True)
        except (Exception, KeyboardInterrupt, asyncio.CancelledError):
            _safe_say('Owned task retirement reported a failure.')
    try:
        run.drive(run.loop.shutdown_asyncgens, retire=True)
    except (Exception, KeyboardInterrupt, asyncio.CancelledError):
        _safe_say('Async-generator retirement reported a failure.')


def main(argv=None):
    parser = _Parser(description='Log in deliberately and save the configured native session.',
                     allow_abbrev=False)
    parser.add_argument('--config', default='config.ini', help='Reader configuration (default: config.ini).')
    parser.add_argument('--replace', action='store_true', help='Permit deliberate replacement after confirmation.')
    args = parser.parse_args(argv)
    try:
        if not sys.stdin.isatty() or threading.current_thread() is not threading.main_thread():
            _safe_say('An interactive terminal in the main thread is required; no login started.')
            return 2
    except (AttributeError, OSError, ValueError):
        return 2
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        _safe_say('Run this command outside an existing event loop.')
        return 2

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    run = _TerminalRun(loop)
    flow = destination = None
    phase, status = 'preflight', 2
    try:
        run.check()
        flow = LoginFlow(args.config)
        run.check()
        destination = LoginDestination(flow._engine._load_config().session_file,
                                       allow_replace=args.replace)
        _say('Session destination: {!r}'.format(str(destination.path)))
        if destination.replacing:
            _say('Replacement requested. All readers must be stopped before saving.')
        run.check()
        phase = 'login'
        if _login(run, flow):
            phase = 'save'
            status = _save(run, flow, destination)
        else:
            status = 3
    except (KeyboardInterrupt, _Stopped, EOFError):
        run.stopped = True
        if destination is not None and destination.outcome.status != 'not_published':
            _safe_report(destination.outcome)
        else:
            _safe_say('Interrupted; session not published.')
        status = 130
    except (LoginError, LoginFileError) as error:
        _safe_say('Stopped: ' + error.kind)
        if destination is not None:
            _safe_report(destination.outcome)
        status = 2 if phase == 'preflight' else 3 if phase == 'login' else 4
    except Exception as error:
        _safe_say('Stopped ({}) during {}.'.format(type(error).__name__, phase))
        if destination is not None:
            _safe_report(destination.outcome)
        status = 2 if phase == 'preflight' else 3 if phase == 'login' else 4
    finally:
        try:
            _retire(run, flow, destination)
        finally:
            run.close()
    return 130 if run.stopped else _effect_exit(destination, status)


if __name__ == '__main__':
    raise SystemExit(main())
