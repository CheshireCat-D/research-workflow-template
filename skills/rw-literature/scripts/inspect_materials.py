#!/usr/bin/env python3
"""Read-only, bounded inventory of local literature files or supplied ZIP members."""
import argparse
import hashlib
import json
import ntpath
import os
from pathlib import Path
import stat
import struct
import sys
import zipfile


MIB = 1024 * 1024
TYPES = {".pdf", ".bib", ".ris", ".md", ".txt", ".tex", ".docx"}
EXCLUDED = {".git", ".agents", ".research", ".venv", "venv", "__pycache__", "node_modules"}
ZIP_METADATA_LIMIT = 8 * MIB


def linked(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def open_regular(path):
    before = path.lstat()
    if linked(before) or not stat.S_ISREG(before.st_mode):
        raise ValueError("Expected a regular file without symbolic links or reparse points")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    stream = os.fdopen(fd, "rb")
    if not stat.S_ISREG(os.fstat(fd).st_mode) or identity(before) != identity(os.fstat(fd)):
        stream.close()
        raise ValueError("File changed before it could be inspected")
    return stream, before


def zip_directory(stream, size):
    """Bound declared directory metadata before ZipFile builds its member objects."""
    stream.seek(max(0, size - 65557))
    tail = stream.read(65557)
    offset = tail.rfind(b"PK\x05\x06")
    while offset >= 0:
        if offset + 22 <= len(tail):
            fields = struct.unpack_from("<4s4H2LH", tail, offset)
            if offset + 22 + fields[-1] == len(tail):
                break
        offset = tail.rfind(b"PK\x05\x06", 0, offset)
    if offset < 0:
        raise ValueError("ZIP end directory record is missing or incomplete")
    if tail[max(0, offset-20):offset-16] == b"PK\x06\x07":
        raise ValueError("ZIP64 directory metadata is unsupported; inspect an extracted folder")
    if fields[1] or fields[2] or fields[3] != fields[4]:
        raise ValueError("Multi-disk ZIP archives are unsupported")
    return {"archive_declared_members": fields[4], "archive_directory_bytes": fields[5]}


def inspect(source, *, max_files=200, max_depth=6, max_file_bytes=64*MIB,
            max_total_bytes=256*MIB, max_entries=5000):
    limits = dict(max_files=max_files, max_depth=max_depth, max_file_bytes=max_file_bytes,
                  max_total_bytes=max_total_bytes, max_entries=max_entries)
    caps = dict(max_files=10000, max_depth=20, max_file_bytes=256*MIB,
                max_total_bytes=1024*MIB, max_entries=50000)
    if any(type(value) is not int or not 0 < value <= caps[name] for name, value in limits.items()):
        raise ValueError("Limits must be positive integers within the documented CLI bounds")
    path = Path(source).absolute()
    initial = path.lstat()
    if linked(initial):
        raise ValueError("The input must not be a symbolic link or reparse point")
    result = {"passed": True, "input": {"name": path.name}, "limits": limits,
              "scope": "File inventory and exact byte identity; original text and citation support remain unexamined.",
              "supported_extensions": sorted(TYPES), "excluded_directories": sorted(EXCLUDED),
              "files": [], "skipped": [], "errors": [], "truncated": False,
              "content_bytes_hashed": 0, "content_bytes_budgeted": 0, "entries_seen": 0}
    result["limits"]["max_zip_directory_bytes"] = ZIP_METADATA_LIMIT

    def skip(name, reason, *, bounded=False, error=False):
        result["errors" if error else "skipped"].append({"path": name, "reason": reason})
        result["truncated"] |= bounded
        result["passed"] &= not error

    def digest(stream, size, limit):
        if size > limit or result["content_bytes_budgeted"] + size > max_total_bytes:
            return None
        # Reserve declared bytes before I/O so a corrupt stream cannot reclaim
        # the total allowance by failing repeatedly near its end.
        result["content_bytes_budgeted"] += size
        value = hashlib.sha256()
        length = 0
        while True:
            chunk = stream.read(min(65536, size - length + 1))
            if not chunk:
                break
            length += len(chunk)
            if length > size:
                raise ValueError("Content grew during inspection")
            value.update(chunk)
            result["content_bytes_hashed"] += len(chunk)
        if length != size:
            raise ValueError("Content size changed during inspection")
        return value.hexdigest()

    def record(name, size, stream):
        item = {"path": name, "kind": Path(name).suffix.lower()[1:], "bytes": size,
                "sha256": None, "reading_status": "not-read", "citation_support": "not-checked"}
        result["files"].append(item)
        try:
            item["sha256"] = digest(stream, size, max_file_bytes)
            item["status"] = "inventoried" if item["sha256"] else "byte-limit"
            result["truncated"] |= item["sha256"] is None
        except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
            item["status"] = "unreadable-or-changed"
            skip(name, str(exc), error=True)

    def eligible():
        if result["entries_seen"] >= max_entries:
            result["truncated"] = True
            return False
        result["entries_seen"] += 1
        return True

    if stat.S_ISDIR(initial.st_mode):
        result["input"]["kind"] = "directory"
        root = path.resolve()
        pending = [(path, 0)]
        while pending:
            directory, depth = pending.pop()
            relative = directory.relative_to(path).as_posix()
            try:
                if linked(directory.lstat()) or not directory.resolve().is_relative_to(root):
                    skip(relative, "linked-directory")
                    continue
                with os.scandir(directory) as entries:
                    for entry in entries:
                        name = (directory / entry.name).relative_to(path).as_posix()
                        if not eligible():
                            pending.clear()
                            break
                        child = Path(entry.path)
                        info = entry.stat(follow_symlinks=False)
                        if linked(info):
                            skip(name, "symbolic-link-or-reparse-point")
                        elif stat.S_ISDIR(info.st_mode) and entry.name not in EXCLUDED:
                            if depth >= max_depth:
                                skip(name, "depth-limit", bounded=True)
                            else:
                                pending.append((child, depth+1))
                        elif stat.S_ISREG(info.st_mode) and child.suffix.lower() in TYPES:
                            if len(result["files"]) >= max_files:
                                skip(name, "file-count-limit", bounded=True)
                                pending.clear()
                                break
                            try:
                                with open_regular(child)[0] as stream:
                                    record(name, info.st_size, stream)
                                    if identity(info) != identity(os.fstat(stream.fileno())):
                                        result["files"][-1].update(status="changed", sha256=None)
                                        skip(name, "File changed during inspection", error=True)
                            except (OSError, ValueError) as exc:
                                skip(name, str(exc), error=True)
            except OSError as exc:
                skip(relative, str(exc), error=True)
    elif stat.S_ISREG(initial.st_mode):
        with open_regular(path)[0] as stream:
            if path.suffix.lower() == ".zip":
                result["input"]["kind"] = "zip"
                archive_hash = digest(stream, initial.st_size, 256*MIB)
                if archive_hash is None:
                    raise ValueError("Archive exceeds the 256 MiB or total byte budget")
                result["input"].update(bytes=initial.st_size, sha256=archive_hash)
                directory = zip_directory(stream, initial.st_size)
                result["input"].update(directory)
                if directory["archive_declared_members"] > max_entries or directory["archive_directory_bytes"] > ZIP_METADATA_LIMIT:
                    skip(path.name, "archive-directory-limit", bounded=True)
                else:
                    stream.seek(0)
                    with zipfile.ZipFile(stream) as archive:
                        seen = set()
                        for member in archive.infolist():
                            name = member.filename
                            if not eligible():
                                break
                            parts = name.rstrip("/").split("/")
                            unsafe = (ntpath.splitdrive(name)[0] or name.startswith("/") or "\\" in name
                                      or any(part in ("", ".", "..") for part in parts))
                            if unsafe or stat.S_ISLNK(member.external_attr >> 16):
                                skip(name, "unsafe-or-linked-archive-member")
                            elif name in seen and not member.is_dir():
                                skip(name, "duplicate-archive-member-name", error=True)
                            elif any(part in EXCLUDED for part in parts[:-1]):
                                skip(name, "excluded-directory")
                            elif len(parts)-1 > max_depth:
                                skip(name, "depth-limit", bounded=True)
                            elif not member.is_dir() and Path(name).suffix.lower() in TYPES:
                                if len(result["files"]) >= max_files:
                                    skip(name, "file-count-limit", bounded=True)
                                    break
                                try:
                                    with archive.open(member) as content:
                                        record(name, member.file_size, content)
                                except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
                                    skip(name, str(exc), error=True)
                            seen.add(name)
            elif path.suffix.lower() in TYPES:
                result["input"]["kind"] = "file"
                result["entries_seen"] = 1
                record(path.name, initial.st_size, stream)
            else:
                raise ValueError("Use a literature file, a directory or a ZIP archive")
            if identity(initial) != identity(os.fstat(stream.fileno())):
                raise ValueError("Input changed during inspection; repeat on a stable copy")
    else:
        raise ValueError("Use a regular literature file, a directory or a ZIP archive")
    result["files"].sort(key=lambda item: item["path"])
    hashes = {}
    for item in result["files"]:
        if item["sha256"]:
            hashes.setdefault(item["sha256"], []).append(item["path"])
    result["duplicates"] = [{"sha256": key, "paths": paths} for key, paths in hashes.items() if len(paths) > 1]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("--max-files", type=int, default=200, help="1–10000; default 200")
    parser.add_argument("--max-depth", type=int, default=6, help="1–20; default 6")
    parser.add_argument("--max-file-bytes", type=int, default=64*MIB, help="1–268435456; default 64 MiB")
    parser.add_argument("--max-total-bytes", type=int, default=256*MIB, help="1–1073741824; default 256 MiB")
    parser.add_argument("--max-entries", type=int, default=5000, help="1–50000; default 5000")
    args = vars(parser.parse_args())
    try:
        result = inspect(args.pop("source"), **args)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        result = {"passed": False, "error": str(exc)}
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
