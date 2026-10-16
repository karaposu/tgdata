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


def _hidden(prompt):
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        return getpass.getpass(prompt, stream=sys.stderr)


def _confirm(prompt, expected='yes'):
    return input(prompt).strip().lower() == expected.lower()


def _drive(loop, awaitable):
    task = asyncio.ensure_future(awaitable, loop=loop)
    stopped = False
    while True:
        try:
            result = loop.run_until_complete(task)
        except KeyboardInterrupt:
            stopped = True
            if not task.done():
                task.cancel()
        except asyncio.CancelledError:
            raise _Stopped() from None
        except BaseException:
            if stopped:
                raise _Stopped() from None
            raise
        else:
            if stopped:
                raise _Stopped()
            return result


def _settle_flow(loop, flow):
    if flow.status.cleanup_pending:
        _drive(loop, flow.close())
    if flow.status.cleanup_pending:
        raise LoginError('cleanup_required')


def _login(loop, flow):
    checked_uncertain = False
    while True:
        _settle_flow(loop, flow)
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
            if checked_uncertain or not _confirm(
                    'Login outcome uncertain. Check authorization without another code? Type yes: '):
                _say('Login outcome uncertain; session not published.')
                return False
            checked_uncertain = True
            try:
                _drive(loop, flow.check_authorization())
            except LoginError as error:
                _say('Authorization check: ' + error.kind)
                if flow.status.step != 'complete':
                    return False
            continue
        if status.step == 'phone':
            value = _hidden('Phone number with country code (hidden): ')
            action = flow.start(value)
        elif status.step == 'code':
            value = _hidden('Telegram code (hidden): ')
            action = flow.submit_code(value)
        elif status.step == 'password':
            value = _hidden('Two-factor password (hidden): ')
            action = flow.submit_password(value)
        else:
            _say('Unsupported login state; session not published.')
            return False
        try:
            _drive(loop, action)
        except LoginError as error:
            _say('Login: ' + error.kind)
            if error.retry_after:
                _say('Retry after {} seconds; no code resent.'.format(error.retry_after))
            _settle_flow(loop, flow)
            if flow.status.step in ('complete', 'uncertain'):
                continue
            if error.kind not in ('invalid_phone', 'invalid_code', 'invalid_password'):
                return False
        finally:
            value = action = None


def _publish(destination, credential, account_id):
    interrupted = [False]
    previous = signal.getsignal(signal.SIGINT)

    def stop(signum, frame):
        interrupted[0] = True

    signal.signal(signal.SIGINT, stop)
    try:
        result = destination.save(credential, account_id,
                                  stop_requested=lambda: interrupted[0])
    finally:
        signal.signal(signal.SIGINT, previous)
    return result, interrupted[0]


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


def main(argv=None):
    parser = _Parser(description='Log in deliberately and save the configured native session.',
                     allow_abbrev=False)
    parser.add_argument('--config', default='config.ini', help='Reader configuration (default: config.ini).')
    parser.add_argument('--replace', action='store_true', help='Permit deliberate replacement after confirmation.')
    args = parser.parse_args(argv)
    try:
        if not sys.stdin.isatty() or threading.current_thread() is not threading.main_thread():
            _say('An interactive terminal in the main thread is required; no login started.')
            return 2
    except (AttributeError, OSError, ValueError):
        return 2
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        _say('Run this command outside an existing event loop.')
        return 2

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    flow = destination = None
    phase = 'preflight'
    old_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        flow = LoginFlow(args.config)
        destination = LoginDestination(flow._engine._load_config().session_file,
                                       allow_replace=args.replace)
        _say('Session destination: {!r}'.format(str(destination.path)))
        if destination.replacing:
            _say('Replacement requested. All readers must be stopped before saving.')
        phase = 'login'
        if not _login(loop, flow):
            return 3
        account_id = flow.status.account_id
        _say('Authenticated account {}.'.format(account_id))
        if destination.replacing and not _confirm(
                'Replace {!r} with account {} after stopping ALL readers? Type REPLACE: '
                .format(str(destination.path), account_id), 'replace'):
            _say('Replacement cancelled; previous session unchanged.')
            return 130
        phase = 'save'
        credential = flow.session_data
        while True:
            result, stopped = _publish(destination, credential, account_id)
            _report(result)
            if stopped or result.error_kind in ('interrupted', 'KeyboardInterrupt'):
                return 130
            if result.status == 'published':
                return 0
            if result.status == 'publication_uncertain':
                return 5
            if not result.retryable or not _confirm(
                    'Retry saving this completed login without another code? Type yes: '):
                return 4
    except (KeyboardInterrupt, _Stopped, EOFError):
        try:
            if destination is not None and destination.outcome.status != 'not_published':
                _report(destination.outcome)
            else:
                _say('Interrupted; session not published.')
        except Exception:
            pass
        return 130
    except (LoginError, LoginFileError) as error:
        _say('Stopped: ' + error.kind)
        if destination is not None and destination.outcome.status != 'not_published':
            _report(destination.outcome)
        return 2 if phase == 'preflight' else 3 if phase == 'login' else 4
    except Exception as error:
        # No raw error text: configuration/source/filesystem exceptions may be secret.
        try:
            _say('Stopped ({}) during {}.'.format(type(error).__name__, phase))
            if destination is not None:
                _report(destination.outcome)
        except Exception:
            pass  # Broken output cannot undo known publication.
        if destination is not None:
            if destination.outcome.status == 'published':
                return 0
            if destination.outcome.status == 'publication_uncertain':
                return 5
        return 2 if phase == 'preflight' else 3 if phase == 'login' else 4
    finally:
        try:
            if flow is not None and flow.status.cleanup_pending:
                try:
                    _drive(loop, flow.close())
                except (Exception, KeyboardInterrupt, asyncio.CancelledError):
                    try:
                        _say('Login cleanup remains incomplete; no further source work started.')
                    except Exception:
                        pass
            if destination is not None:
                before = destination.outcome
                result = destination.close()
                if result.cleanup_warning and not before.cleanup_warning:
                    try:
                        _report(result)
                    except Exception:
                        pass
            pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
            for task in pending:
                task.cancel()
            if pending:
                try:
                    _drive(loop, asyncio.gather(*pending, return_exceptions=True))
                except (Exception, KeyboardInterrupt, asyncio.CancelledError):
                    pass
            try:
                _drive(loop, loop.shutdown_asyncgens())
            except (Exception, KeyboardInterrupt, asyncio.CancelledError):
                pass
        finally:
            loop.close()
            asyncio.set_event_loop(None)
            signal.signal(signal.SIGINT, old_handler)


if __name__ == '__main__':
    raise SystemExit(main())
