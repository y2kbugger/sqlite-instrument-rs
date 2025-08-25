import pytest
import sqlite3
import tempfile
import os
import sys

from pathlib import Path
from typing import Iterator


@pytest.fixture(scope="session")
def extension_path() -> Path:
    project_root = Path(__file__).parent.parent

    if sys.platform == 'linux':
        debug_path = project_root / "target" / "debug" / "libsqlite_instrument_rs.so"
        release_path = project_root / "target" / "release" / "libsqlite_instrument_rs.so"
    else:
        raise NotImplementedError(f"Unsupported platform: {sys.platform}")

    candidates = []

    if debug_path.exists():
        candidates.append((debug_path, debug_path.stat().st_mtime, "debug"))

    if release_path.exists():
        candidates.append((release_path, release_path.stat().st_mtime, "release"))

    if not candidates:
        pytest.exit(
            f"No SQLite extension found. Expected at:\n"
            f"  Debug: {debug_path}\n"
            f"  Release: {release_path}\n"
            f"Run 'cargo build' or 'cargo build --release' first."
        )


    candidates.sort(key=lambda x: x[1], reverse=True)
    newest_path, mtime, build_type = candidates[0]
    return newest_path


@pytest.fixture
def temp_db_path() -> Iterator[Path]:
    fd, temp_path = tempfile.mkstemp(suffix='.db', prefix='test_sqlite_')

    try:
        os.close(fd)
        os.unlink(temp_path)

        yield Path(temp_path)

    finally:
        if Path(temp_path).exists():
            os.unlink(temp_path)


@pytest.fixture
def sqlite_connection(extension_path: Path, temp_db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(temp_db_path))

    try:
        conn.enable_load_extension(True)
        conn.load_extension(str(extension_path))

        yield conn

    finally:
        conn.close()


@pytest.fixture
def cursor(sqlite_connection: sqlite3.Connection) -> Iterator[sqlite3.Cursor]:
    cursor = sqlite_connection.cursor()
    try:
        yield cursor
    finally:
        cursor.close()
