from tuplesaver.engine import Engine
from tuplesaver.sql import select
from conftest import ExecutionCount


def test_instrumentation_tables_exist(client_engine: Engine):
    ecs = client_engine.query(*select(ExecutionCount)).fetchall()
    assert len(ecs) == 0
