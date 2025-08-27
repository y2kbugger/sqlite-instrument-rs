from tuplesaver.engine import Engine
from tuplesaver.sql import select
from conftest import ExecutionCount
from sqlite_log_capture import SqliteErrorLogCapture


def test_instrumentation_tables_exist(trace_engine: Engine):
    ecs = trace_engine.query(*select(ExecutionCount)).fetchall()
    assert len(ecs) == 0

def test_names_of_each_db(client_engine: Engine, trace_engine: Engine):
    client_db_path = client_engine.connection.execute("PRAGMA database_list").fetchone()[2]
    trace_db_path = trace_engine.connection.execute("PRAGMA database_list").fetchone()[2]


    print(f"Main DB path: {client_db_path}")
    print(f"Trace DB path: {trace_db_path}")

    assert client_db_path.endswith('.db')
    assert trace_db_path.endswith('.trace.db')

    # Verify trace database path is based on main database path
    assert trace_db_path == client_db_path.replace('.db', '.trace.db')


def test_trace_log(client_engine: Engine, trace_engine: Engine, sqlite_logged: SqliteErrorLogCapture):
    with sqlite_logged:
        client_engine.connection.execute("SELECT 1")

    logs = set(sqlite_logged.get_messages())

    expected_logs = {
        'DEBUG: STMT traced - SELECT 1',
        'DEBUG: PROFILE traced - SELECT 1'
    }

    assert logs == expected_logs
