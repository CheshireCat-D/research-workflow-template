"""Bounded JSON I/O and POSIX project-local atomic mutations; no network or exec."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import uuid

JSON_LIMIT = 8 * 1024 * 1024
FILE_LIMIT = 256 * 1024 * 1024


class CoreError(Exception):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
        super().__init__(message)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + repr(key))
        result[key] = value
    return result


def _constant(value):
    raise ValueError('non-finite JSON number: ' + value)


def parse_json(data: bytes):
    if len(data) > JSON_LIMIT:
        raise CoreError('json_too_large', 'JSON exceeds the 8 MiB metadata limit')
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise CoreError('invalid_json', str(exc)) from exc


def json_bytes(value):
    try:
        result = (json.dumps(value, ensure_ascii=False, allow_nan=False,
                             sort_keys=True, indent=2) + '\n').encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise CoreError('invalid_json', str(exc)) from exc
    if len(result) > JSON_LIMIT:
        raise CoreError('json_too_large', 'JSON exceeds the 8 MiB metadata limit')
    return result


def sha(data: bytes):
    return hashlib.sha256(data).hexdigest()


def object_sha(value):
    return sha(json_bytes(value))


def path_parts(relative: str):
    if (not isinstance(relative, str) or not relative or '\\' in relative or
            '\x00' in relative or ':' in relative or relative.startswith('/')):
        raise CoreError('unsafe_path', 'Expected a project-relative POSIX file path')
    parts = relative.split('/')
    if any(part in ('', '.', '..') for part in parts) or PurePosixPath(relative).is_absolute():
        raise CoreError('unsafe_path', 'Empty, dot and parent path components are not allowed')
    return parts


def read_input(path):
    """Read a bounded explicit JSON input, or standard input for the exact ``-`` name."""
    try:
        if path == '-':
            # Read bytes so the same UTF-8 and 8 MiB checks apply to files and
            # pipes. Do not close the process-owned stdin stream.
            return parse_json(sys.stdin.buffer.read(JSON_LIMIT + 1))
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise CoreError('input_unreadable', 'The supplied JSON input must be a regular file')
        with os.fdopen(fd, 'rb') as stream:
            return parse_json(stream.read(JSON_LIMIT + 1))
    except OSError as exc:
        raise CoreError('input_unreadable', 'Cannot read the supplied JSON input') from exc


class ProjectFiles:
    """Anchor every nested operation to a directory fd; never follow internal links."""
    def __init__(self, root):
        if os.name != 'posix':
            raise CoreError('unsupported_platform', 'D1 writes require POSIX/macOS/Linux')
        try:
            self.root = Path(root).resolve(strict=True)
            self.fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except (OSError, RuntimeError) as exc:
            raise CoreError('invalid_root', 'Project root must be an existing directory') from exc

    def close(self):
        os.close(self.fd)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @contextmanager
    def parent(self, relative, *, create=False):
        parts = path_parts(relative)
        fd = os.dup(self.fd)
        try:
            for part in parts[:-1]:
                if create:
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=fd)
                    except FileExistsError:
                        pass
                try:
                    next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                except FileNotFoundError:
                    raise
                except OSError as exc:
                    raise CoreError('unsafe_path', 'A path component is a link or not a directory') from exc
                os.close(fd)
                fd = next_fd
            yield fd, parts[-1]
        finally:
            os.close(fd)

    def _open(self, relative):
        with self.parent(relative) as (parent, name):
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            except FileNotFoundError:
                raise
            except OSError as exc:
                raise CoreError('unsafe_path', 'Cannot safely open project file: ' + relative) from exc
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise CoreError('unsafe_path', 'Project resource must be a regular file: ' + relative)
        return fd

    def read(self, relative):
        with os.fdopen(self._open(relative), 'rb') as stream:
            data = stream.read(JSON_LIMIT + 1)
        if len(data) > JSON_LIMIT:
            raise CoreError('json_too_large', 'Metadata file exceeds 8 MiB: ' + relative)
        return data

    def fingerprint(self, relative):
        result, total = hashlib.sha256(), 0
        with os.fdopen(self._open(relative), 'rb') as stream:
            before = os.fstat(stream.fileno())
            while chunk := stream.read(1024 * 1024):
                total += len(chunk)
                if total > FILE_LIMIT:
                    raise CoreError('file_too_large', 'Local fingerprint exceeds 256 MiB; use a controlled/external reference')
                result.update(chunk)
            after = os.fstat(stream.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise CoreError('concurrent_change', 'Resource changed while being fingerprinted: ' + relative)
        return result.hexdigest()

    def identity(self, relative):
        """Identity of a safely opened regular file, including hardlink aliases."""
        fd = self._open(relative)
        try:
            value = os.fstat(fd)
            return value.st_dev, value.st_ino
        finally:
            os.close(fd)

    def directory_identity(self, relative):
        with self.parent(relative + '/_identity') as (fd, _):
            value = os.fstat(fd)
            return value.st_dev, value.st_ino

    def internal_identities(self):
        """Read current metadata identities without following links or creating state."""
        identities = {self.identity('project.json'), self.identity('records/registry.json')}
        try:
            state_identity = self.directory_identity('.research')
        except FileNotFoundError:
            return identities, None
        # Keep names, not open descriptors, for sibling state directories.
        pending, visited = ['.research'], 0
        while pending:
            relative = pending.pop()
            with self.parent(relative + '/_identity') as (fd, _):
                with os.scandir(fd) as entries:
                    for entry in entries:
                        visited += 1
                        if visited > 4096:
                            raise CoreError('state_too_large', 'Internal state exceeds the 4096-entry identity check limit')
                        value = entry.stat(follow_symlinks=False)
                        if stat.S_ISREG(value.st_mode):
                            identities.add((value.st_dev, value.st_ino))
                        elif stat.S_ISDIR(value.st_mode):
                            pending.append(relative + '/' + entry.name)
        return identities, state_identity

    def write(self, relative, data):
        """Write one file atomically. Callers hold the project writer lock."""
        with self.parent(relative, create=True) as (parent, name):
            try:
                prior = os.stat(name, dir_fd=parent, follow_symlinks=False)
                if not stat.S_ISREG(prior.st_mode):
                    raise CoreError('unsafe_path', 'Refusing to replace a link or non-file: ' + relative)
            except FileNotFoundError:
                pass
            temporary = '.rw-' + uuid.uuid4().hex
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=parent)
            try:
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
                os.fsync(parent)
            finally:
                try:
                    os.unlink(temporary, dir_fd=parent)
                except FileNotFoundError:
                    pass

    @contextmanager
    def lock(self):
        import fcntl
        with self.parent('.research/write.lock', create=True) as (parent, name):
            try:
                fd = os.open(name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                             0o600, dir_fd=parent)
            except OSError as exc:
                raise CoreError('unsafe_path', 'Cannot safely open project writer lock') from exc
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise CoreError('unsafe_path', 'Writer lock is not a regular file')
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise CoreError('project_busy', 'Another writer is active; retry after it completes') from exc
            yield
        finally:
            os.close(fd)
