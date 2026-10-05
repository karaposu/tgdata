"""Complete, non-replacing publication of local batch artifacts."""

import hashlib
import os
from pathlib import Path
import stat
import tempfile


_HASH_CHUNK = 1024 * 1024


class BatchStorageError(RuntimeError):
    """A local artifact preparation/integrity failure, not a Telegram verdict."""

    def __init__(self, message):
        super().__init__(message)
        self.partial_result = None
        self.__suppress_context__ = True


def prepare_directory(directory):
    if directory is None or isinstance(directory, bool) or directory == '':
        raise BatchStorageError('an explicit output directory is required')
    try:
        root = Path(directory).expanduser().resolve()
    except TypeError:
        raise BatchStorageError('output directory must be a filesystem path') from None
    root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
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
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise BatchStorageError('existing artifact is not a regular nonsymlink file')
    descriptor = os.open(str(path), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(descriptor, 'rb') as stored:
        opened = os.fstat(stored.fileno())
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
        os.link(str(temp_path), str(destination))
    except FileExistsError:
        _verify_existing(destination, digest, size)
    return destination


def _remove_temp(path):
    if path is not None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


async def download_blob(directory, writer, expected_size=None):
    """Await writer(file_object), then publish exactly its completed bytes.

    The writer must return the supplied file object, as Telethon 1.45.0's
    photo/document download paths do. Hashing and publication use bounded-memory
    synchronous local I/O after the asynchronous download completes.
    """
    root = prepare_directory(directory)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w+b', dir=str(root), prefix='.tgdata-media-', delete=False) as output:
            temporary = Path(output.name)
            result = await writer(output)
            if result is not output or output.closed:
                raise BatchStorageError('the requested media did not produce its output file')
            output.flush()
            os.fsync(output.fileno())
            output.seek(0)
            digest, size = _hash_stream(output)
            if expected_size is not None and size != expected_size:
                raise BatchStorageError('downloaded media size differs from its declared size')
        _publish(temporary, root / digest, digest, size)
        return {'sha256': digest, 'size': size, 'path': digest}
    finally:
        _remove_temp(temporary)


def save_manifest(directory, batch_id, data):
    """Publish canonical manifest bytes under their already-validated batch ID."""
    root = prepare_directory(directory)
    temporary = None
    digest = hashlib.sha256(data).hexdigest()
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=str(root), prefix='.tgdata-manifest-', delete=False) as output:
            temporary = Path(output.name)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        return _publish(temporary, root / (batch_id + '.json'), digest, len(data))
    finally:
        _remove_temp(temporary)
