import pytest

from codebs.ingestion import rules


@pytest.mark.parametrize(
    "name",
    [
        ".env",
        ".env.local",
        ".ENV",
        "server.pem",
        "deploy.key",
        "id_rsa",
        "id_ed25519",
        "credentials.json",
        ".npmrc",
        ".pypirc",
        ".netrc",
    ],
)
def test_sensitive_names_are_detected(name):
    assert rules.is_sensitive_name(name)


@pytest.mark.parametrize(
    "name",
    [".env.example", ".env.sample", ".env.template", "environment.py", "keyboard.py"],
)
def test_ordinary_names_are_not_sensitive(name):
    assert not rules.is_sensitive_name(name)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("main.py", "python"),
        ("App.TSX", "typescript"),
        ("Dockerfile", "dockerfile"),
        ("Makefile", "makefile"),
        ("data.weird", "unknown"),
        ("README", "unknown"),
    ],
)
def test_language_detection(name, expected):
    assert rules.detect_language(name) == expected


def test_excluded_directory_names_include_extras():
    assert rules.is_excluded_directory_name("node_modules", frozenset())
    assert rules.is_excluded_directory_name("vendor", frozenset({"vendor"}))
    assert not rules.is_excluded_directory_name("src", frozenset())