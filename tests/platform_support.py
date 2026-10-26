"""Narrow capability handling for real cross-platform security fixtures."""
import os


def symlink_or_skip(test, link, target, *, target_is_directory=False):
    """Create a real link; skip only a Windows account lacking link privilege.

    Native Windows junction rejection, ordinary project operations and writer
    exclusion have separate tests and remain mandatory on Windows.
    """
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except OSError as exc:
        if os.name == 'nt' and getattr(exc, 'winerror', None) == 1314:
            test.skipTest('This Windows account lacks symbolic-link creation privilege; native junction rejection is tested separately')
        raise
