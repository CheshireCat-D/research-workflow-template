"""Native Windows storage with no-follow handles and nonblocking writer locks.

Directory handles omit FILE_SHARE_DELETE, retaining the checked path chain until
an operation ends. All reparse points (including junctions) are rejected. This is
local filesystem protection, not a transaction against malicious administrators,
network filesystem failures or power loss.
"""
from __future__ import annotations

from contextlib import contextmanager
import ctypes
from ctypes import wintypes
from functools import lru_cache
import os
from pathlib import Path
import stat
import uuid

from .storage import CoreError, PosixProjectFiles, path_parts

REPARSE_POINT = 0x400
DIRECTORY = 0x10
GENERIC_READ, GENERIC_WRITE = 0x80000000, 0x40000000
# Attribute-only handles are exempt from Windows share-access restrictions.
# Request FILE_LIST_DIRECTORY as well, so omission of FILE_SHARE_DELETE really
# blocks renaming a checked directory while its guard is held.
DIRECTORY_ACCESS = 0x1 | 0x80
OPEN_EXISTING, OPEN_ALWAYS, CREATE_NEW = 3, 4, 1
_RESERVED = {'CON', 'PRN', 'AUX', 'NUL', 'CLOCK$', 'CONIN$', 'CONOUT$'}
_RESERVED.update(prefix + number for prefix in ('COM', 'LPT')
                 for number in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '¹', '²', '³'))


def validate_windows_parts(relative):
    """Keep portable '/' record paths and reject Win32 name aliases/devices."""
    parts = path_parts(relative)
    for part in parts:
        device = part.split('.', 1)[0].rstrip(' .').upper()
        if (part.endswith((' ', '.')) or device in _RESERVED or
                any(ord(char) < 32 or char in '<>"|?*' for char in part)):
            raise CoreError('unsafe_path', 'Windows device names, aliases and special characters are not project paths')
    return parts


def is_reparse(value):
    return bool(getattr(value, 'st_file_attributes', 0) & REPARSE_POINT)


class _FileInfo(ctypes.Structure):
    _fields_ = [('attributes', wintypes.DWORD), ('creation', wintypes.FILETIME),
                ('access', wintypes.FILETIME), ('write', wintypes.FILETIME),
                ('volume', wintypes.DWORD), ('size_high', wintypes.DWORD),
                ('size_low', wintypes.DWORD), ('links', wintypes.DWORD),
                ('index_high', wintypes.DWORD), ('index_low', wintypes.DWORD)]


class _Overlapped(ctypes.Structure):
    _fields_ = [('Internal', ctypes.c_size_t), ('InternalHigh', ctypes.c_size_t),
                ('Offset', wintypes.DWORD), ('OffsetHigh', wintypes.DWORD),
                ('hEvent', wintypes.HANDLE)]


@lru_cache(maxsize=1)
def _api():
    if os.name != 'nt':
        raise CoreError('unsupported_platform', 'Native Windows handles require Windows')
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                               wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    api.CreateFileW.restype = wintypes.HANDLE
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL
    api.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(_FileInfo)]
    api.GetFileInformationByHandle.restype = wintypes.BOOL
    api.GetFileType.argtypes = [wintypes.HANDLE]
    api.GetFileType.restype = wintypes.DWORD
    api.LockFileEx.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                              wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(_Overlapped)]
    api.LockFileEx.restype = wintypes.BOOL
    api.UnlockFileEx.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                                wintypes.DWORD, ctypes.POINTER(_Overlapped)]
    api.UnlockFileEx.restype = wintypes.BOOL
    api.MoveFileExW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
    api.MoveFileExW.restype = wintypes.BOOL
    return api


def _native(path):
    value = str(path)
    if value.startswith('\\\\?\\'):
        return value
    if value.startswith('\\\\'):
        return '\\\\?\\UNC\\' + value[2:]
    return '\\\\?\\' + value


def _error(path):
    code = ctypes.get_last_error()
    if code in (2, 3):
        return FileNotFoundError(2, 'The project resource does not exist', str(path))
    if code in (80, 183):
        return FileExistsError(17, 'The project resource already exists', str(path))
    return ctypes.WinError(code)


def _info(handle):
    value = _FileInfo()
    if not _api().GetFileInformationByHandle(handle, ctypes.byref(value)):
        raise _error('open handle')
    return value


def _identity(handle):
    value = _info(handle)
    return value.volume, (value.index_high << 32) | value.index_low


def _open_handle(path, *, directory=False, access=GENERIC_READ, creation=OPEN_EXISTING):
    # OPEN_REPARSE_POINT opens the reparse object itself, instead of its target.
    flags = 0x00200000 | (0x02000000 if directory else 0x80)
    handle = _api().CreateFileW(_native(path), access, 0x1 | 0x2, None, creation, flags, None)
    if handle == ctypes.c_void_p(-1).value:
        raise _error(path)
    try:
        info = _info(handle)
        if (info.attributes & REPARSE_POINT or bool(info.attributes & DIRECTORY) != directory or
                (not directory and _api().GetFileType(handle) != 1)):
            raise CoreError('unsafe_path', 'A project resource is a reparse point or has the wrong type')
        return handle
    except BaseException:
        _api().CloseHandle(handle)
        raise


def _to_fd(handle, flags):
    import msvcrt
    try:
        return msvcrt.open_osfhandle(handle, flags | os.O_BINARY)
    except BaseException:
        _api().CloseHandle(handle)
        raise


class WindowsProjectFiles(PosixProjectFiles):
    """Keep checked directories open against rename while using native paths."""
    is_windows = True

    def __init__(self, root):
        self._root_handles = []
        try:
            candidate = Path(root).absolute()
            if is_reparse(candidate.lstat()):
                raise CoreError('unsafe_path', 'The project root must not be a reparse point')
            self.root = candidate.resolve(strict=True)
            if not self.root.is_dir():
                raise CoreError('invalid_root', 'Project root must be an existing directory')
            # Keep ancestors as well as the root open. No ancestor may be swapped
            # for a junction between validation and a subsequent absolute open.
            current = Path(self.root.anchor)
            for component in (None, *self.root.parts[1:]):
                if component is not None:
                    current = current / component
                self._root_handles.append(_open_handle(current, directory=True, access=DIRECTORY_ACCESS))
        except BaseException as exc:
            self.close()
            if isinstance(exc, (CoreError, KeyboardInterrupt, SystemExit)):
                raise
            raise CoreError('invalid_root', 'Project root must be an existing accessible directory') from exc

    def close(self):
        for handle in reversed(self._root_handles):
            _api().CloseHandle(handle)
        self._root_handles.clear()

    @contextmanager
    def checked_directory(self, relative='', *, create=False):
        parts = validate_windows_parts(relative) if relative else []
        handles, current = [], self.root
        try:
            if not self._root_handles:
                raise CoreError('invalid_root', 'Project directory guard is closed')
            for part in parts:
                current = current / part
                if create:
                    try:
                        current.mkdir(mode=0o700)
                    except FileExistsError:
                        pass
                try:
                    handles.append(_open_handle(current, directory=True, access=DIRECTORY_ACCESS))
                except FileNotFoundError:
                    raise
                except OSError as exc:
                    raise CoreError('unsafe_path', 'Cannot safely open project directory') from exc
            yield current
        finally:
            for handle in reversed(handles):
                _api().CloseHandle(handle)

    @contextmanager
    def parent(self, relative, *, create=False):
        parts = validate_windows_parts(relative)
        with self.checked_directory('/'.join(parts[:-1]), create=create) as parent:
            yield parent, parts[-1]

    def _open(self, relative):
        with self.parent(relative) as (parent, name):
            try:
                handle = _open_handle(parent / name)
            except FileNotFoundError:
                raise
            except OSError as exc:
                raise CoreError('unsafe_path', 'Cannot safely open project file: ' + relative) from exc
            return _to_fd(handle, os.O_RDONLY)

    def identity(self, relative):
        import msvcrt
        fd = self._open(relative)
        try:
            return _identity(msvcrt.get_osfhandle(fd))
        finally:
            os.close(fd)

    def directory_identity(self, relative):
        with self.checked_directory(relative) as directory:
            handle = _open_handle(directory, directory=True, access=DIRECTORY_ACCESS)
            try:
                return _identity(handle)
            finally:
                _api().CloseHandle(handle)

    def internal_identities(self):
        identities = {self.identity('project.json'), self.identity('records/registry.json')}
        try:
            state_identity = self.directory_identity('.research')
        except FileNotFoundError:
            return identities, None
        pending, visited = ['.research'], 0
        while pending:
            relative = pending.pop()
            with self.checked_directory(relative) as directory, os.scandir(directory) as entries:
                for entry in entries:
                    visited += 1
                    if visited > 4096:
                        raise CoreError('state_too_large', 'Internal state exceeds the 4096-entry identity check limit')
                    value = entry.stat(follow_symlinks=False)
                    if is_reparse(value):
                        raise CoreError('unsafe_path', 'Internal state contains a reparse point')
                    child = relative + '/' + entry.name
                    if stat.S_ISREG(value.st_mode):
                        identities.add(self.identity(child))
                    elif stat.S_ISDIR(value.st_mode):
                        pending.append(child)
        return identities, state_identity

    def write(self, relative, data):
        with self.parent(relative, create=True) as (parent, name):
            target = parent / name
            try:
                prior = _open_handle(target)
            except FileNotFoundError:
                pass
            else:
                _api().CloseHandle(prior)
            temporary = parent / ('.rw-' + uuid.uuid4().hex)
            handle = _open_handle(temporary, access=GENERIC_WRITE, creation=CREATE_NEW)
            try:
                with os.fdopen(_to_fd(handle, os.O_WRONLY), 'wb') as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                if not _api().MoveFileExW(_native(temporary), _native(target), 0x1 | 0x8):
                    raise _error(target)
            finally:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass

    @contextmanager
    def lock(self):
        # LockFileEx may lock beyond EOF, so a new lock file stays empty. No
        # bootstrap write or stale-file deletion is needed to acquire the lock.
        with self.parent('.research/write.lock', create=True) as (parent, name):
            try:
                handle = _open_handle(parent / name, access=GENERIC_READ | GENERIC_WRITE,
                                      creation=OPEN_ALWAYS)
            except OSError as exc:
                raise CoreError('unsafe_path', 'Cannot safely open project writer lock') from exc
            overlap, locked = _Overlapped(), False
            try:
                if not _api().LockFileEx(handle, 0x2 | 0x1, 0, 1, 0, ctypes.byref(overlap)):
                    code = ctypes.get_last_error()
                    if code in (32, 33, 997):
                        raise CoreError('project_busy', 'Another writer is active; retry after it completes')
                    raise ctypes.WinError(code)
                locked = True
                yield
            finally:
                if locked:
                    _api().UnlockFileEx(handle, 0, 1, 0, ctypes.byref(overlap))
                _api().CloseHandle(handle)
