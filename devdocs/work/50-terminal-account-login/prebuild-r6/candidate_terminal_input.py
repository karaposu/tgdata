"""Private, bounded POSIX input; values leave only after terminal settlement."""
import os
import select
import sys

try:
    import termios
except ImportError:
    termios = None

_LIMIT = 128


class TerminalInputError(Exception):
    def __init__(self, kind):
        self.kind = kind
        super().__init__(kind)


class TerminalStopped(EOFError):
    pass


def _validate(fd, attrs):
    if os.tcgetpgrp(fd) != os.getpgrp():
        raise TerminalInputError('terminal_not_foreground')
    flags, local = attrs[0], attrs[3]
    forbidden = termios.IGNCR | termios.INLCR | termios.ISTRIP | getattr(termios, 'IUCLC', 0)
    if (not local & termios.ICANON or not local & termios.ISIG
            or not flags & termios.ICRNL or flags & forbidden
            or os.fpathconf(fd, 'PC_MAX_CANON') <= _LIMIT + 2):
        raise TerminalInputError('terminal_mode_unsupported')


def _open_terminal():
    if termios is None or os.name != 'posix':
        raise TerminalInputError('terminal_unsupported')
    fd = None
    try:
        fd = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        attrs = termios.tcgetattr(fd)
        _validate(fd, attrs)
        return fd, attrs
    except BaseException:
        if fd is not None:
            os.close(fd)
        raise


def terminal_preflight():
    fd = None
    try:
        fd, unused = _open_terminal()
    except TerminalInputError:
        raise
    except Exception:
        raise TerminalInputError('terminal_unavailable') from None
    finally:
        if fd is not None:
            os.close(fd)


def read_hidden(prompt, stop_requested):
    fd = original = None
    value = None
    cleanup_error = None
    try:
        try:
            fd, original = _open_terminal()
            if stop_requested():
                raise TerminalStopped()
            hidden = original[:]
            hidden[3] &= ~(termios.ECHO | termios.ECHONL)
            # Original settings are retained before a possibly partial mutation.
            termios.tcsetattr(fd, termios.TCSANOW, hidden)
            actual = termios.tcgetattr(fd)
            if actual != hidden:
                raise TerminalInputError('terminal_hide_failed')
            if stop_requested():
                raise TerminalStopped()
            print(prompt, end='', file=sys.stderr, flush=True)
            while True:
                if stop_requested():
                    raise TerminalStopped()
                ready, unused_w, unused_x = select.select([fd], [], [], 0.05)
                if stop_requested():
                    raise TerminalStopped()
                if not ready:
                    continue
                try:
                    data = os.read(fd, _LIMIT + 2)
                except BlockingIOError:
                    continue
                if stop_requested():
                    raise TerminalStopped()
                if len(data) > _LIMIT + 1 or (len(data) > _LIMIT and not data.endswith(b'\n')):
                    raise TerminalInputError('terminal_input_too_long')
                if not data or not data.endswith(b'\n'):
                    raise TerminalStopped()
                try:
                    value = data[:-1].decode('utf-8', errors='strict')
                except UnicodeError:
                    raise TerminalInputError('terminal_input_encoding') from None
                print(file=sys.stderr, flush=True)
                break
        except (TerminalInputError, TerminalStopped):
            raise
        except Exception:
            raise TerminalInputError('terminal_input_failed') from None
    finally:
        if fd is not None:
            if original is not None:
                try:
                    termios.tcflush(fd, termios.TCIFLUSH)
                except Exception:
                    cleanup_error = 'terminal_flush_failed'
                try:
                    termios.tcsetattr(fd, termios.TCSANOW, original)
                    if termios.tcgetattr(fd) != original:
                        cleanup_error = 'terminal_restore_failed'
                except Exception:
                    cleanup_error = 'terminal_restore_failed'
            try:
                os.close(fd)
            except Exception:
                if cleanup_error is None:
                    cleanup_error = 'terminal_close_failed'
        if cleanup_error is not None:
            raise TerminalInputError(cleanup_error) from None
    if stop_requested():
        raise TerminalStopped()
    return value
