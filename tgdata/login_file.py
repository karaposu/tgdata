"""Private native-file publication for a completed, operator-owned login."""

from contextlib import contextmanager
from dataclasses import dataclass, replace
import hashlib
import os
from pathlib import Path
import stat
import tempfile

from telethon.sessions import SQLiteSession
from telethon.tl import types

from .session_store import StoredSession


class LoginFileError(RuntimeError):
    def __init__(self, kind, *, retryable=False):
        self.kind, self.retryable = kind, retryable
        super().__init__(kind)
        self.__suppress_context__ = True


@dataclass(frozen=True)
class Publication:
    status: str
    destination: str
    account_id: int = None
    error_kind: str = None
    retryable: bool = False
    recovery_directory: str = None
    cleanup_warning: bool = False


def _sync_directory(path):
    fd = os.open(str(path), os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _sync_file(path):
    with open(str(path), 'rb') as stream:
        os.fsync(stream.fileno())


def _signature(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns


def _snapshot(path):
    try:
        before = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(before.st_mode):
        raise LoginFileError('destination_not_regular')
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or _signature(opened) != _signature(before):
            raise LoginFileError('destination_changed')
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
        if _signature(os.fstat(stream.fileno())) != _signature(opened):
            raise LoginFileError('destination_changed')
    return _signature(opened), digest.hexdigest()


@contextmanager
def _native_session(path):
    # Retain the object even if native construction/commit fails, so its opened
    # sqlite3 connection can still be retired without a second implicit commit.
    session = SQLiteSession.__new__(SQLiteSession)
    primary = None
    try:
        SQLiteSession.__init__(session, str(path))
        yield session
    except BaseException as error:
        primary = error
        raise
    finally:
        connection = getattr(session, '_conn', None)
        close_error = None
        try:
            if connection is not None:
                session.close()
        except BaseException as error:
            close_error = error
        finally:
            if connection is not None:
                try:
                    connection.close()
                except BaseException:
                    # Do not remove a candidate whose writer may still be open.
                    raise LoginFileError('candidate_cleanup_required') from None
        if primary is None and close_error is not None:
            raise close_error


class _CredentialStore:
    def __init__(self, value):
        self._value = value

    def load(self, name):
        return self._value


def _source(credential, account_id):
    source = StoredSession(_CredentialStore(credential), 'completed-login')
    if (type(account_id) is not int or not 0 < account_id < 2**63
            or not source.auth_key or len(source.auth_key.key) != 256
            or type(source.dc_id) is not int or source.dc_id <= 0
            or type(source.server_address) is not str or not source.server_address
            or type(source.port) is not int or not 1 <= source.port <= 65535
            or source.get_entity_rows_by_id(0) != (0, account_id)):
        raise LoginFileError('invalid_completed_credential')
    own = source.get_entity_rows_by_id(account_id)
    if own is not None and (type(own) not in (tuple, list) or len(own) != 2
                            or own[0] != account_id or type(own[1]) is not int
                            or not -2**63 <= own[1] < 2**63):
        raise LoginFileError('invalid_completed_credential')
    return source, own


def _prepare_candidate(path, credential, account_id):
    source, own = _source(credential, account_id)
    states = list(source.get_update_states())
    with _native_session(path) as target:
        target.set_dc(source.dc_id, source.server_address, source.port)
        target.auth_key = source.auth_key
        target.takeout_id = source.takeout_id
        peers = [types.InputPeerUser(0, account_id)]
        if own is not None:
            peers.append(types.InputPeerUser(account_id, own[1]))
        target.process_entities(peers)
        for ident, state in states:
            target.set_update_state(ident, state)
        target.save()
    with _native_session(path) as restored:
        if ((restored.dc_id, restored.server_address, restored.port) !=
                (source.dc_id, source.server_address, source.port)
                or not restored.auth_key or restored.auth_key.key != source.auth_key.key
                or restored.takeout_id != source.takeout_id
                or restored.get_entity_rows_by_id(0) != (0, account_id)
                or restored.get_entity_rows_by_id(account_id) != own):
            raise LoginFileError('candidate_verification_failed')
        expected = {ident: (s.pts, s.qts, s.date.timestamp(), s.seq) for ident, s in states}
        actual = {ident: (s.pts, s.qts, s.date.timestamp(), s.seq)
                  for ident, s in restored.get_update_states()}
        if actual != expected:
            raise LoginFileError('candidate_verification_failed')
    _sync_file(path)


class LoginDestination:
    """One private publication lifetime; not a lock for ordinary readers."""

    def __init__(self, session_name, *, allow_replace=False):
        self.directory = None
        self._owned = set()
        self._retain = False
        self.outcome = None
        if (os.name != 'posix' or not hasattr(os, 'O_NOFOLLOW')
                or not all(hasattr(os, name) for name in ('link', 'replace', 'fsync'))):
            raise LoginFileError('unsupported_filesystem')
        if type(session_name) is not str or not session_name:
            raise LoginFileError('invalid_destination')
        name = session_name if session_name.endswith('.session') else session_name + '.session'
        absolute = Path(os.path.abspath(name))  # Match reader CWD; never expand '~'.
        self._requested_parent = absolute.parent
        self.parent = absolute.parent.resolve(strict=True)
        self.path = self.parent / absolute.name
        parent_stat = self.parent.stat()
        if not stat.S_ISDIR(parent_stat.st_mode):
            raise LoginFileError('invalid_parent')
        self._parent_identity = parent_stat.st_dev, parent_stat.st_ino
        self._sidecars()
        self._initial = _snapshot(self.path)
        self.replacing = self._initial is not None
        if self.replacing and not allow_replace:
            raise LoginFileError('destination_exists_use_replace')
        self.outcome = Publication('not_published', str(self.path))
        try:
            self.directory = Path(tempfile.mkdtemp(prefix='.tgdata-login-', dir=str(self.parent)))
            os.chmod(str(self.directory), 0o700)
            # Persist the recovery directory's own name, not only its contents.
            _sync_directory(self.parent)
            self._probe()
        except BaseException:
            self.close()
            raise

    def _probe(self):
        names = [self.directory / name for name in ('probe-a', 'probe-b', 'probe-c')]
        self._owned.update(names)
        fd = os.open(str(names[0]), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        os.link(str(names[0]), str(names[1]))
        os.replace(str(names[1]), str(names[2]))
        _sync_directory(self.directory)
        for path in names:
            try:
                path.unlink()
            except FileNotFoundError:
                pass

    def _sidecars(self):
        for suffix in ('-wal', '-shm', '-journal'):
            try:
                Path(str(self.path) + suffix).lstat()
            except FileNotFoundError:
                continue
            raise LoginFileError('sqlite_sidecar_present')

    def _check(self):
        current = self.parent.stat()
        if (self._requested_parent.resolve(strict=True) != self.parent
                or (current.st_dev, current.st_ino) != self._parent_identity):
            raise LoginFileError('parent_changed')
        self._sidecars()
        if _snapshot(self.path) != self._initial:
            raise LoginFileError('destination_changed')

    def _failure(self, account_id, error, *, uncertain=False):
        kind = error.kind if isinstance(error, LoginFileError) else type(error).__name__
        retryable = not uncertain and (error.retryable if isinstance(error, LoginFileError)
                                       else isinstance(error, OSError))
        if uncertain or kind == 'candidate_cleanup_required':
            self._retain = True
        self.outcome = Publication('publication_uncertain' if uncertain else 'not_published',
            str(self.path), account_id, kind, retryable and not self._retain,
            str(self.directory) if self._retain else None)
        return self.outcome

    def save(self, credential, account_id, *, stop_requested=None):
        if self._retain or self.outcome.status == 'published':
            return self.outcome
        attempted = False
        try:
            def check_stop():
                if stop_requested is not None and stop_requested():
                    raise LoginFileError('interrupted')

            check_stop()
            self._check()
            fd, name = tempfile.mkstemp(prefix='candidate-', suffix='.session', dir=str(self.directory))
            os.close(fd)
            candidate = Path(name)
            self._owned.add(candidate)
            self._owned.update(Path(name + s) for s in ('-journal', '-wal', '-shm'))
            os.chmod(name, 0o600)
            _prepare_candidate(candidate, credential, account_id)
            self._check()
            check_stop()
            if self.replacing:
                backup = self.directory / 'previous.session'
                if backup not in self._owned:
                    os.link(str(self.path), str(backup))
                    self._owned.add(backup)
                if _snapshot(backup) != self._initial:
                    raise LoginFileError('destination_changed')
                _sync_file(backup)
                _sync_directory(self.directory)
                self._check()
                check_stop()
                attempted = True
                os.replace(str(candidate), str(self.path))
            else:
                attempted = True
                try:
                    os.link(str(candidate), str(self.path))
                except FileExistsError:
                    # Atomic no-clobber refusal establishes that we did not publish.
                    attempted = False
                    raise LoginFileError('destination_changed') from None
            _sync_directory(self.parent)
            self.outcome = Publication('published', str(self.path), account_id)
        except (Exception, KeyboardInterrupt) as error:
            return self._failure(account_id, error, uncertain=attempted)
        self.close()
        return self.outcome

    def close(self):
        if self.directory is None or self._retain:
            return self.outcome
        failed = False
        for path in sorted(self._owned):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except (Exception, KeyboardInterrupt):
                failed = True
        try:
            self.directory.rmdir()
        except FileNotFoundError:
            pass
        except (Exception, KeyboardInterrupt):
            failed = True
        if failed and self.outcome is not None:
            self.outcome = replace(self.outcome, cleanup_warning=True,
                                   recovery_directory=str(self.directory))
        return self.outcome
