import dataclasses

import pytest

from codebs.ingestion.models import (
    EntryKind,
    EntryStatus,
    FileRecord,
    SkipReason,
    WalkConfig,
    WalkResult,
)


def included_file(path: str = "src/app.py") -> FileRecord:
    return FileRecord(
        path=path,
        kind=EntryKind.FILE,
        status=EntryStatus.INCLUDED,
        language="python",
        size_bytes=120,
    )


def skipped_file(reason: SkipReason, path: str = "uv.lock") -> FileRecord:
    return FileRecord(
        path=path,
        kind=EntryKind.FILE,
        status=EntryStatus.SKIPPED,
        skip_reason=reason,
    )


def test_skip_reason_values_are_stable():
    assert {reason.value for reason in SkipReason} == {
        "excluded_directory",
        "sensitive",
        "symlink",
        "lockfile",
        "minified",
        "too_large",
        "binary",
        "unreadable",
        "gitignored",
    }


def test_walk_config_defaults_match_design_note():
    config = WalkConfig()

    assert config.max_file_size_bytes == 1_048_576
    assert config.binary_sniff_bytes == 8_192
    assert config.extra_excluded_dirs == frozenset()
    assert config.respect_gitignore is False


@pytest.mark.parametrize("field_name", ["max_file_size_bytes", "binary_sniff_bytes"])
@pytest.mark.parametrize("bad_value", [0, -1])
def test_walk_config_rejects_non_positive_values(field_name, bad_value):
    with pytest.raises(ValueError, match=field_name):
        WalkConfig(**{field_name: bad_value})


def test_file_record_is_immutable():
    record = included_file()

    with pytest.raises(dataclasses.FrozenInstanceError):
        record.path = "other.py"


def test_skipped_record_requires_a_reason():
    with pytest.raises(ValueError, match="skip_reason"):
        FileRecord(
            path="uv.lock",
            kind=EntryKind.FILE,
            status=EntryStatus.SKIPPED,
        )


def test_included_record_rejects_a_reason():
    with pytest.raises(ValueError, match="skip_reason"):
        FileRecord(
            path="src/app.py",
            kind=EntryKind.FILE,
            status=EntryStatus.INCLUDED,
            skip_reason=SkipReason.BINARY,
        )


def test_records_with_the_same_values_are_equal():
    assert included_file() == included_file()
    assert included_file("a.py") != included_file("b.py")


def test_walk_result_counts_included_and_skipped():
    result = WalkResult(
        records=(
            included_file("a.py"),
            included_file("b.py"),
            skipped_file(SkipReason.LOCKFILE),
        )
    )

    assert result.included_count == 2
    assert result.skipped_count == 1


def test_empty_walk_result_has_zero_counts():
    result = WalkResult(records=())

    assert result.included_count == 0
    assert result.skipped_count == 0