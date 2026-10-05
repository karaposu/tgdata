"""Complete, non-replacing publication of local batch artifacts."""

from contextlib import contextmanager
from functools import partial
import hashlib
import logging
import os
from pathlib import Path
import stat
import tempfile


_HASH_CHUNK = 1024 * 1024
logger = logging.getLogger(__name__)


class BatchStorageError(RuntimeError):
    """A local artifact preparation/integrity failure, not a Telegram verdict."""

    def __init__(self, message):
        super().__init__(message)
        self.partial_result = None
        self.__suppress_context__ = True


def _local_io(action, *args, **kwargs):
    """Preserve a local failure without inheriting a caller's RPC context.

    Only owned synchronous filesystem actions belong here. In particular,
    awaiting the SDK writer here would erase meaningful transport causes.
    """
    try:
        return action(*args, **kwargs)
    except Exception as error:
        raise error from None


class _LocalFile:
    """Mark local stream operations, including writes invoked by the SDK."""

    def __init__(self, stream):
        self._stream = stream

    def __getattr__(self, name):
        value = _local_io(getattr, self._stream, name)
        return partial(_local_io, value) if callable(value) else value


def _warn_cleanup(operation, error):
    # Cleanup diagnostics must never replace the already chosen outcome.
    # No paths, exception text or traceback: they may contain sensitive data.
    try:
        logger.warning('Batch artifact cleanup failed during %s (%s)', operation, type(error).__name__)
    except BaseException:
        pass


def _cleanup(stream, temporary, primary):
    first = None
    actions = [('close', lambda: stream.close())]
    if temporary is not None:
        actions.append(('unlink', partial(os.unlink, temporary)))
    for operation, action in actions:
        try:
            _local_io(action)
        except Exception as error:
            if operation == 'unlink' and isinstance(error, FileNotFoundError):
                continue
            if primary is not None or first is not None:
                _warn_cleanup(operation, error)
            else:
                first = error
    if first is not None:
        raise first from None


@contextmanager
def _owned_stream(stream, temporary=None):
    primary = None
    try:
        yield _LocalFile(stream)
    except BaseException as error:
        primary = error
        raise
    finally:
        _cleanup(stream, temporary, primary)


def prepare_directory(directory):
    if directory is None or isinstance(directory, bool) or directory == '':
        raise BatchStorageError('an explicit output directory is required')
    try:
        root = _local_io(lambda: Path(directory).expanduser().resolve())
    except TypeError:
        raise BatchStorageError('output directory must be a filesystem path') from None
    _local_io(root.mkdir, parents=True, exist_ok=True)
    if not _local_io(root.is_dir):
        raise BatchStorageError('output path is not a directory')
    return root


def _hash_stream(stream):
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = stream.read(_HASH_CHUNK)
        if not chunk:
            break
        size += len(chunk)
        digest.update(chunk)
    return digest.hexdigest(), size


def _verify_existing(path, expected_digest, expected_size):
    # Do not follow a cache entry that somebody replaced with a symlink.
    before = _local_io(path.lstat)
    if not stat.S_ISREG(before.st_mode):
        raise BatchStorageError('existing artifact is not a regular nonsymlink file')
    def nofollow(name, flags):
        return os.open(name, flags | getattr(os, 'O_NOFOLLOW', 0))

    # Builtin open owns descriptor handoff, including failures constructing the
    # stream. The shared owner also protects a read error from a failed close.
    raw = _local_io(open, str(path), 'rb', opener=nofollow)
    with _owned_stream(raw) as stored:
        opened = _local_io(os.fstat, stored.fileno())
        if (not stat.S_ISREG(opened.st_mode)
                or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)):
            raise BatchStorageError('existing artifact changed during verification')
        if opened.st_size != expected_size:
            raise BatchStorageError('existing artifact failed size verification')
        digest, size = _hash_stream(stored)
    if digest != expected_digest or size != expected_size:
        raise BatchStorageError('existing artifact failed content verification')


def _publish(temp_path, destination, digest, size):
    try:
        _local_io(os.link, str(temp_path), str(destination))
    except FileExistsError:
        _verify_existing(destination, digest, size)
    return destination


async def download_blob(directory, writer, expected_size=None):
    """Await writer(file_object), then publish exactly its completed bytes.

    The writer must return the supplied file object, as Telethon 1.45.0's
    photo/document download paths do. Hashing and publication use bounded-memory
    synchronous local I/O after the asynchronous download completes.
    """
    root = prepare_directory(directory)
    raw = _local_io(tempfile.NamedTemporaryFile, mode='w+b', dir=str(root), prefix='.tgdata-media-', delete=False)
    with _owned_stream(raw, raw.name) as output:
        result = await writer(output)
        if result is not output or output.closed:
            raise BatchStorageError('the requested media did not produce its output file')
        output.flush()
        _local_io(os.fsync, output.fileno())
        output.seek(0)
        digest, size = _hash_stream(output)
        if expected_size is not None and size != expected_size:
            raise BatchStorageError('downloaded media size differs from its declared size')
        output.close()
        _publish(raw.name, root / digest, digest, size)
        return {'sha256': digest, 'size': size, 'path': digest}


def save_manifest(directory, batch_id, data):
    """Publish canonical manifest bytes under their already-validated batch ID."""
    root = prepare_directory(directory)
    digest = hashlib.sha256(data).hexdigest()
    raw = _local_io(tempfile.NamedTemporaryFile, mode='wb', dir=str(root), prefix='.tgdata-manifest-', delete=False)
    with _owned_stream(raw, raw.name) as output:
        output.write(data)
        output.flush()
        _local_io(os.fsync, output.fileno())
        output.close()
        return _publish(raw.name, root / (batch_id + '.json'), digest, len(data))
