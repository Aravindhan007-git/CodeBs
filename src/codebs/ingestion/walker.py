"""Walk a repository directory and classify every entry."""

import os
from pathlib import Path

from codebs.ingestion import rules
from codebs.ingestion.models import (
    EntryKind,
    EntryStatus,
    FileRecord,
    SkipReason,
    WalkConfig,
    WalkResult,
)


def walk_repository(root: Path, config: WalkConfig | None = None) -> WalkResult:
    """Return an inventory of the files under ``root``."""
    settings = config or WalkConfig()
    root_path = Path(root)
    if not root_path.exists():
        raise FileNotFoundError(f"Repository root does not exist: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Repository root is not a directory: {root_path}")

    records: list[FileRecord] = []
    _walk(_list_entries(root_path), root_path, settings, records)
    records.sort(key=lambda record: record.path)
    return WalkResult(records=tuple(records))


def _list_entries(directory: str | os.PathLike[str]) -> list[os.DirEntry[str]]:
    with os.scandir(directory) as iterator:
        return sorted(iterator, key=lambda entry: entry.name)


def _walk(
    entries: list[os.DirEntry[str]],
    root: Path,
    config: WalkConfig,
    records: list[FileRecord],
) -> None:
    for entry in entries:
        relative = Path(entry.path).relative_to(root).as_posix()
        if entry.is_symlink():
            kind = EntryKind.DIRECTORY if _points_to_directory(entry) else EntryKind.FILE
            records.append(_skipped(relative, kind, SkipReason.SYMLINK))
        elif entry.is_dir(follow_symlinks=False):
            _handle_directory(entry, relative, root, config, records)
        elif entry.is_file(follow_symlinks=False):
            records.append(_classify_file(entry, relative))
        else:
            records.append(_skipped(relative, EntryKind.FILE, SkipReason.UNREADABLE))


def _handle_directory(
    entry: os.DirEntry[str],
    relative: str,
    root: Path,
    config: WalkConfig,
    records: list[FileRecord],
) -> None:
    is_virtualenv = os.path.isfile(os.path.join(entry.path, rules.VIRTUALENV_MARKER))
    if is_virtualenv or rules.is_excluded_directory_name(
        entry.name, config.extra_excluded_dirs
    ):
        records.append(
            _skipped(relative, EntryKind.DIRECTORY, SkipReason.EXCLUDED_DIRECTORY)
        )
        return
    try:
        children = _list_entries(entry.path)
    except OSError:
        records.append(_skipped(relative, EntryKind.DIRECTORY, SkipReason.UNREADABLE))
        return
    _walk(children, root, config, records)


def _classify_file(entry: os.DirEntry[str], relative: str) -> FileRecord:
    name = entry.name
    if rules.is_sensitive_name(name):
        return _skipped(relative, EntryKind.FILE, SkipReason.SENSITIVE)
    if rules.is_lockfile_name(name):
        return _skipped(relative, EntryKind.FILE, SkipReason.LOCKFILE)
    if rules.is_minified_name(name):
        return _skipped(relative, EntryKind.FILE, SkipReason.MINIFIED)
    try:
        size = entry.stat().st_size
    except OSError:
        return _skipped(relative, EntryKind.FILE, SkipReason.UNREADABLE)
    return FileRecord(
        path=relative,
        kind=EntryKind.FILE,
        status=EntryStatus.INCLUDED,
        language=rules.detect_language(name),
        size_bytes=size,
    )


def _points_to_directory(entry: os.DirEntry[str]) -> bool:
    try:
        return entry.is_dir()
    except OSError:
        return False


def _skipped(relative: str, kind: EntryKind, reason: SkipReason) -> FileRecord:
    return FileRecord(
        path=relative,
        kind=kind,
        status=EntryStatus.SKIPPED,
        skip_reason=reason,
    )