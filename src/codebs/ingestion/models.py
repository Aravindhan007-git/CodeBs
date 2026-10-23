"""Data types for the repository walker."""

from dataclasses import dataclass, field
from enum import StrEnum

DEFAULT_MAX_FILE_SIZE_BYTES = 1_048_576
DEFAULT_BINARY_SNIFF_BYTES = 8_192


class EntryKind(StrEnum):
    FILE = "file"
    DIRECTORY = "directory"


class EntryStatus(StrEnum):
    INCLUDED = "included"
    SKIPPED = "skipped"


class SkipReason(StrEnum):
    EXCLUDED_DIRECTORY = "excluded_directory"
    SENSITIVE = "sensitive"
    SYMLINK = "symlink"
    LOCKFILE = "lockfile"
    MINIFIED = "minified"
    TOO_LARGE = "too_large"
    BINARY = "binary"
    UNREADABLE = "unreadable"
    GITIGNORED = "gitignored"


@dataclass(frozen=True)
class FileRecord:
    """One entry discovered by the walker.

    ``path`` is relative to the repository root and always uses forward
    slashes, so records look the same on every operating system.
    """

    path: str
    kind: EntryKind
    status: EntryStatus
    skip_reason: SkipReason | None = None
    language: str | None = None
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.status is EntryStatus.SKIPPED and self.skip_reason is None:
            raise ValueError("A skipped entry must have a skip_reason.")
        if self.status is EntryStatus.INCLUDED and self.skip_reason is not None:
            raise ValueError("An included entry must not have a skip_reason.")


@dataclass(frozen=True)
class WalkConfig:
    """Settings that control what the walker includes."""

    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES
    binary_sniff_bytes: int = DEFAULT_BINARY_SNIFF_BYTES
    extra_excluded_dirs: frozenset[str] = field(default_factory=frozenset)
    respect_gitignore: bool = False

    def __post_init__(self) -> None:
        if self.max_file_size_bytes <= 0:
            raise ValueError(
                f"max_file_size_bytes must be positive, got {self.max_file_size_bytes}."
            )
        if self.binary_sniff_bytes <= 0:
            raise ValueError(
                f"binary_sniff_bytes must be positive, got {self.binary_sniff_bytes}."
            )


@dataclass(frozen=True)
class WalkResult:
    """The outcome of one walk: every recorded entry, in sorted order."""

    records: tuple[FileRecord, ...]

    @property
    def included_count(self) -> int:
        return sum(1 for record in self.records if record.status is EntryStatus.INCLUDED)

    @property
    def skipped_count(self) -> int:
        return sum(1 for record in self.records if record.status is EntryStatus.SKIPPED)