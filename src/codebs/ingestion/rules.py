"""Pure classification rules for the repository walker.

Nothing here touches the filesystem, so every rule can be tested with plain
strings.
"""

from fnmatch import fnmatchcase
from pathlib import PurePosixPath

EXCLUDED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "htmlcov",
        "node_modules",
        ".next",
        "dist",
        "build",
        "target",
        ".idea",
        ".vscode",
    }
)

VIRTUALENV_MARKER = "pyvenv.cfg"

SENSITIVE_NAME_PATTERNS = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa*",
    "id_ed25519*",
    "credentials.json",
    ".npmrc",
    ".pypirc",
    ".netrc",
)

SENSITIVE_ALLOWED_NAMES = frozenset({".env.example", ".env.sample", ".env.template"})

LOCKFILE_NAMES = frozenset(
    {
        "uv.lock",
        "poetry.lock",
        "pipfile.lock",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "cargo.lock",
        "composer.lock",
        "gemfile.lock",
        "go.sum",
    }
)

MINIFIED_NAME_PATTERNS = ("*.min.js", "*.min.css", "*.map")

BINARY_EXTENSIONS = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".ico",
        ".webp",
        ".tiff",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".7z",
        ".rar",
        ".jar",
        ".war",
        ".whl",
        ".egg",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".o",
        ".obj",
        ".a",
        ".lib",
        ".class",
        ".pyc",
        ".pyo",
        ".pyd",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".eot",
        ".mp3",
        ".mp4",
        ".wav",
        ".ogg",
        ".mov",
        ".avi",
        ".mkv",
        ".webm",
        ".flac",
        ".db",
        ".sqlite",
        ".sqlite3",
        ".bin",
        ".iso",
        ".dmg",
        ".psd",
    }
)

UNKNOWN_LANGUAGE = "unknown"

LANGUAGE_BY_FILENAME = {
    "Dockerfile": "dockerfile",
    "Makefile": "makefile",
    "Pipfile": "toml",
}

LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".sh": "shell",
    ".ps1": "powershell",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".xml": "xml",
    ".md": "markdown",
    ".rst": "restructuredtext",
    ".txt": "text",
}


def is_excluded_directory_name(name: str, extra_excluded: frozenset[str]) -> bool:
    return name in EXCLUDED_DIRECTORY_NAMES or name in extra_excluded


def is_sensitive_name(name: str) -> bool:
    lowered = name.lower()
    if lowered in SENSITIVE_ALLOWED_NAMES:
        return False
    return any(fnmatchcase(lowered, pattern) for pattern in SENSITIVE_NAME_PATTERNS)


def is_lockfile_name(name: str) -> bool:
    return name.lower() in LOCKFILE_NAMES


def is_minified_name(name: str) -> bool:
    lowered = name.lower()
    return any(fnmatchcase(lowered, pattern) for pattern in MINIFIED_NAME_PATTERNS)

def is_binary_extension(name: str) -> bool:
    return PurePosixPath(name).suffix.lower() in BINARY_EXTENSIONS


def looks_binary(head: bytes) -> bool:
    return b"\x00" in head


def detect_language(name: str) -> str:
    if name in LANGUAGE_BY_FILENAME:
        return LANGUAGE_BY_FILENAME[name]
    suffix = PurePosixPath(name).suffix.lower()
    return LANGUAGE_BY_EXTENSION.get(suffix, UNKNOWN_LANGUAGE)