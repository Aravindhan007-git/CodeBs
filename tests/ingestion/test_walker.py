import os
from pathlib import Path

import pytest

from codebs.ingestion.models import (
    EntryKind,
    EntryStatus,
    FileRecord,
    SkipReason,
    WalkConfig,
    WalkResult,
)
from codebs.ingestion.walker import walk_repository


def make_file(root: Path, relative: str, content: str = "x") -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content.encode("utf-8"))


def by_path(result: WalkResult) -> dict[str, FileRecord]:
    return {record.path: record for record in result.records}


def test_normal_file_is_included_with_language_and_size(tmp_path):
    make_file(tmp_path, "src/app.py", "x = 1")

    record = by_path(walk_repository(tmp_path))["src/app.py"]

    assert record.status is EntryStatus.INCLUDED
    assert record.kind is EntryKind.FILE
    assert record.language == "python"
    assert record.size_bytes == 5
    assert record.skip_reason is None


def test_excluded_directory_is_one_record_and_never_entered(tmp_path):
    make_file(tmp_path, "node_modules/pkg/index.js")
    make_file(tmp_path, "src/app.py")

    result = walk_repository(tmp_path)

    assert [record.path for record in result.records] == ["node_modules", "src/app.py"]
    skipped = by_path(result)["node_modules"]
    assert skipped.kind is EntryKind.DIRECTORY
    assert skipped.skip_reason is SkipReason.EXCLUDED_DIRECTORY


def test_virtualenv_is_pruned_by_marker_file_whatever_its_name(tmp_path):
    make_file(tmp_path, "myenv/pyvenv.cfg", "home = x")
    make_file(tmp_path, "myenv/lib/site.py")

    result = walk_repository(tmp_path)

    assert [record.path for record in result.records] == ["myenv"]
    assert result.records[0].skip_reason is SkipReason.EXCLUDED_DIRECTORY


def test_extra_excluded_directories_are_pruned(tmp_path):
    make_file(tmp_path, "vendor/lib.py")
    config = WalkConfig(extra_excluded_dirs=frozenset({"vendor"}))

    records = by_path(walk_repository(tmp_path, config))

    assert records["vendor"].skip_reason is SkipReason.EXCLUDED_DIRECTORY


def test_sensitive_files_are_skipped_but_env_example_is_kept(tmp_path):
    make_file(tmp_path, ".env")
    make_file(tmp_path, ".env.example")
    make_file(tmp_path, "server.pem")

    records = by_path(walk_repository(tmp_path))

    assert records[".env"].skip_reason is SkipReason.SENSITIVE
    assert records["server.pem"].skip_reason is SkipReason.SENSITIVE
    assert records[".env.example"].status is EntryStatus.INCLUDED


def test_lockfiles_are_skipped(tmp_path):
    make_file(tmp_path, "uv.lock")
    make_file(tmp_path, "web/package-lock.json")

    records = by_path(walk_repository(tmp_path))

    assert records["uv.lock"].skip_reason is SkipReason.LOCKFILE
    assert records["web/package-lock.json"].skip_reason is SkipReason.LOCKFILE


def test_minified_files_are_skipped(tmp_path):
    make_file(tmp_path, "static/app.min.js")
    make_file(tmp_path, "static/app.js.map")
    make_file(tmp_path, "static/app.js")

    records = by_path(walk_repository(tmp_path))

    assert records["static/app.min.js"].skip_reason is SkipReason.MINIFIED
    assert records["static/app.js.map"].skip_reason is SkipReason.MINIFIED
    assert records["static/app.js"].status is EntryStatus.INCLUDED


def test_unknown_extension_is_included_as_unknown(tmp_path):
    make_file(tmp_path, "notes.weird")

    record = by_path(walk_repository(tmp_path))["notes.weird"]

    assert record.status is EntryStatus.INCLUDED
    assert record.language == "unknown"


def test_hidden_config_directories_are_kept(tmp_path):
    make_file(tmp_path, ".github/workflows/ci.yml")

    record = by_path(walk_repository(tmp_path))[".github/workflows/ci.yml"]

    assert record.status is EntryStatus.INCLUDED
    assert record.language == "yaml"


def test_paths_use_forward_slashes(tmp_path):
    make_file(tmp_path, "pkg/sub/mod.py")

    assert "pkg/sub/mod.py" in by_path(walk_repository(tmp_path))


def test_results_are_sorted_by_path(tmp_path):
    make_file(tmp_path, "b.py")
    make_file(tmp_path, "c/d.py")
    make_file(tmp_path, "a.py")

    paths = [record.path for record in walk_repository(tmp_path).records]

    assert paths == ["a.py", "b.py", "c/d.py"]


def test_missing_root_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        walk_repository(tmp_path / "does-not-exist")


def test_file_as_root_raises(tmp_path):
    make_file(tmp_path, "file.txt")

    with pytest.raises(NotADirectoryError):
        walk_repository(tmp_path / "file.txt")


def test_symlinks_are_skipped_and_never_followed(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    make_file(outside, "secret.txt")
    repo = tmp_path / "repo"
    repo.mkdir()
    make_file(repo, "real.py")
    try:
        (repo / "link_file.txt").symlink_to(outside / "secret.txt")
        (repo / "link_dir").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are not available in this environment.")

    records = by_path(walk_repository(repo))

    assert records["link_file.txt"].skip_reason is SkipReason.SYMLINK
    assert records["link_dir"].skip_reason is SkipReason.SYMLINK
    assert records["link_dir"].kind is EntryKind.DIRECTORY
    assert "link_dir/secret.txt" not in records
    assert records["real.py"].status is EntryStatus.INCLUDED


def test_unreadable_directory_is_recorded_and_the_walk_continues(tmp_path, monkeypatch):
    make_file(tmp_path, "locked/x.py")
    make_file(tmp_path, "ok.py")
    real_scandir = os.scandir

    def fake_scandir(path):
        if Path(path).name == "locked":
            raise PermissionError("denied")
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", fake_scandir)

    records = by_path(walk_repository(tmp_path))

    assert records["locked"].skip_reason is SkipReason.UNREADABLE
    assert records["locked"].kind is EntryKind.DIRECTORY
    assert "locked/x.py" not in records
    assert records["ok.py"].status is EntryStatus.INCLUDED