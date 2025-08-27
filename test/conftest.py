import pytest
import tempfile
import os
import platform
from sqlite_log_capture import SqliteErrorLogCapture

from pathlib import Path
from tuplesaver.engine import Engine
from typing import NamedTuple
from typing import Iterator


def pytest_configure(config):
    config.EXTENSION_PATH = find_extension_path()
    print(f"Extension path: {config.EXTENSION_PATH}")


def find_extension_path() -> Path:
    project_root = Path(__file__).parent.parent

    if platform.system() == 'Linux':
        debug_path = project_root / "target" / "debug" / "libsqlite_instrument_rs.so"
        release_path = project_root / "target" / "release" / "libsqlite_instrument_rs.so"
    else:
        raise NotImplementedError(f"Unsupported platform: {platform.system()}")

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
def extension_path(request) -> Path:
    assert request.config.EXTENSION_PATH is not None
    return request.config.EXTENSION_PATH


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
def sqlite_logged():
    return SqliteErrorLogCapture()


class ExecutionCount(NamedTuple):
    id: int | None
    hash: str | None
    exe_count: int | None
    sql_text: str | None

@pytest.fixture
def client_engine(extension_path: Path, temp_db_path: Path) -> Iterator[Engine]:
    engine = None
    try:
        engine = Engine(temp_db_path)
        engine.connection.enable_load_extension(True)
        engine.connection.load_extension(str(extension_path))

        yield engine
    finally:
        if engine is not None:
            engine.connection.close()


@pytest.fixture
def trace_engine(client_engine: Engine, temp_db_path: Path) -> Iterator[Engine]:
    # Loading the extension in client_engine should create the trace database
    # Now we can check that the trace database has the expected tables
    engine = None
    try:
        engine = Engine(temp_db_path.with_suffix('.trace.db'))

        yield engine
    finally:
        if engine is not None:
            engine.connection.close()
