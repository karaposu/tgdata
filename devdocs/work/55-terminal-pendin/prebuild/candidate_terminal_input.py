"""Private bounded terminal input, retired before a value is admitted."""
import os
import select
import sys

try:
    import termios
except ImportError:
    termios = None

_LIMIT = 128


class TerminalInputError(Exception):
    def __init__(self, kind, *, operation_kind=None, cleanup_kinds=()):
        self.kind = kind
        self.operation_kind = operation_kind
        self.cleanup_kinds = tuple(cleanup_kinds)
        super().__init__(kind)


class TerminalStopped(EOFError):
    pass


def _control(value):
    if isinstance(value, bytes) and len(value) == 1:
        return value[0]
    if type(value) is int and 0 <= value <= 255:
        return value
    raise TerminalInputError('terminal_controls_unsupported')


def _validate(fd, attrs):
    if os.tcgetpgrp(fd) != os.getpgrp():
        raise TerminalInputError('terminal_not_foreground')
    # The kernel may report pending input; the owned flush settles it while hidden.
    allowed = 0
    for name in ('ECHO', 'ECHOE', 'ECHOK', 'ECHONL', 'ECHOCTL', 'ECHOKE',
                 'ECHOPRT', 'ISIG', 'ICANON', 'IEXTEN', 'NOFLSH', 'TOSTOP', 'PENDIN'):
        allowed |= getattr(termios, name, 0)
    forbidden = (termios.ISTRIP | termios.IGNCR | termios.INLCR
                 | termios.PARMRK | getattr(termios, 'IUCLC', 0))
    if (attrs[3] & ~allowed or not attrs[3] & termios.ICANON
            or not attrs[3] & termios.ISIG or not attrs[0] & termios.ICRNL
            or attrs[0] & forbidden or attrs[2] & termios.CSIZE != termios.CS8):
        raise TerminalInputError('terminal_mode_unsupported')
    controls = tuple(_control(attrs[6][i]) for i in
                     (termios.VERASE, termios.VKILL, termios.VEOF, termios.VINTR))
    if (len(set(controls)) != 4 or controls[3] != 3
            or any(v in (10, 13) or not (0 < v < 32 or v == 127) for v in controls)):
        raise TerminalInputError('terminal_controls_unsupported')
    disabled = os.fpathconf(fd, 'PC_VDISABLE')
    if type(disabled) is not int or not 0 <= disabled <= 255 or disabled in controls:
        raise TerminalInputError('terminal_controls_unsupported')
    return controls, disabled


def _open_terminal():
    if termios is None or os.name != 'posix':
        raise TerminalInputError('terminal_unsupported')
    fd = None
    try:
        fd = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        attrs = termios.tcgetattr(fd)
        controls, disabled = _validate(fd, attrs)
        return fd, attrs, controls, disabled
    except BaseException as error:
        operation = error.kind if isinstance(error, TerminalInputError) else 'terminal_unavailable'
        if fd is not None:
            try:
                os.close(fd)
            except Exception:
                raise TerminalInputError('terminal_close_failed', operation_kind=operation,
                                         cleanup_kinds=('terminal_close_failed',)) from None
        if isinstance(error, TerminalInputError) or not isinstance(error, Exception):
            raise
        raise TerminalInputError(operation) from None


def terminal_preflight():
    fd, unused_attrs, unused_controls, unused_disabled = _open_terminal()
    try:
        os.close(fd)
    except Exception:
        raise TerminalInputError('terminal_close_failed',
                                 cleanup_kinds=('terminal_close_failed',)) from None


def read_hidden(prompt, stop_requested):
    fd = original = hidden = None
    mutated = False
    operation_kind = None
    cleanup = []
    value = None
    try:
        try:
            fd, original, controls, disabled = _open_terminal()
            erase, kill, eof, unused_intr = controls
            if stop_requested():
                raise TerminalStopped()
            hidden = original[:]
            hidden[6] = original[6][:]
            hidden[0] &= ~(termios.IXON | termios.IXOFF | getattr(termios, 'IXANY', 0))
            hidden[3] &= ~(termios.ECHO | termios.ECHONL | termios.ICANON | termios.IEXTEN)
            hidden[6][termios.VMIN] = 1
            hidden[6][termios.VTIME] = 0
            hidden[6][termios.VQUIT] = bytes([disabled])
            hidden[6][termios.VSUSP] = bytes([disabled])
            if stop_requested():
                raise TerminalStopped()
            mutated = True
            termios.tcsetattr(fd, termios.TCSANOW, hidden)
            if termios.tcgetattr(fd) != hidden:
                raise TerminalInputError('terminal_hide_failed')
            if stop_requested():
                raise TerminalStopped()
            termios.tcflush(fd, termios.TCIFLUSH)
            if stop_requested():
                raise TerminalStopped()
            print(prompt, end='', file=sys.stderr, flush=True)
            data = bytearray()
            reason = None
            finished = False
            while not finished:
                if stop_requested():
                    raise TerminalStopped()
                ready, unused_w, unused_x = select.select([fd], [], [], 0.05)
                if stop_requested():
                    raise TerminalStopped()
                if not ready:
                    continue
                try:
                    chunk = os.read(fd, 256)
                except BlockingIOError:
                    continue
                if not chunk:
                    raise TerminalStopped()
                for byte in chunk:
                    if stop_requested():
                        raise TerminalStopped()
                    if byte == 10:
                        finished = True
                        break
                    if byte == eof:
                        raise TerminalStopped()
                    if reason is not None:
                        continue
                    if byte == kill:
                        data.clear()
                        continue
                    if byte == erase:
                        try:
                            shorter = data.decode('utf-8')[:-1].encode('utf-8')
                        except UnicodeError:
                            reason = 'terminal_input_encoding'
                        else:
                            data[:] = shorter
                    elif byte < 32 or byte == 127:
                        reason = 'terminal_input_control'
                    elif len(data) >= _LIMIT:
                        reason = 'terminal_input_too_long'
                    else:
                        data.append(byte)
                    if reason is not None:
                        data.clear()
                        print('\nInput rejected; finishing this line. Ctrl-C stops.',
                              file=sys.stderr, flush=True)
            print(file=sys.stderr, flush=True)
            if reason is not None:
                raise TerminalInputError(reason)
            try:
                value = data.decode('utf-8')
            except UnicodeError:
                raise TerminalInputError('terminal_input_encoding') from None
        except TerminalStopped:
            operation_kind = 'input_stopped'
            raise
        except TerminalInputError as error:
            operation_kind = error.kind
            raise
        except Exception:
            operation_kind = 'terminal_input_failed'
            raise TerminalInputError(operation_kind) from None
    finally:
        if fd is not None:
            if mutated:
                try:
                    termios.tcflush(fd, termios.TCIFLUSH)
                except Exception:
                    cleanup.append('terminal_flush_failed')
                try:
                    # Keep all protected controls until the FINAL mode write.
                    settling = hidden[:]
                    settling[6] = hidden[6][:]
                    settling[3] = (settling[3] & ~termios.ICANON) | (original[3] & termios.ICANON)
                    termios.tcsetattr(fd, termios.TCSANOW, settling)
                    termios.tcflush(fd, termios.TCIFLUSH)
                except Exception:
                    cleanup.append('terminal_restore_failed')
                try:
                    termios.tcsetattr(fd, termios.TCSANOW, original)
                    if termios.tcgetattr(fd) != original:
                        cleanup.append('terminal_restore_failed')
                except Exception:
                    cleanup.append('terminal_restore_failed')
            try:
                os.close(fd)
            except Exception:
                cleanup.append('terminal_close_failed')
        if cleanup:
            kinds = tuple(dict.fromkeys(cleanup))
            kind = 'terminal_restore_failed' if 'terminal_restore_failed' in kinds else kinds[0]
            raise TerminalInputError(kind, operation_kind=operation_kind, cleanup_kinds=kinds) from None
    if stop_requested():
        raise TerminalStopped()
    return value
