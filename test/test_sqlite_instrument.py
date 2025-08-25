from tuplesaver.engine import Engine
from tuplesaver.sql import select
from conftest import ExecutionCount


def test_instrumentation_tables_exist(trace_engine: Engine):
    ecs = trace_engine.query(*select(ExecutionCount)).fetchall()
    assert len(ecs) == 0
