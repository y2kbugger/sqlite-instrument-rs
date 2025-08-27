#!/usr/bin/env python3
import sqlite3
from timeit import repeat
from pathlib import Path


REPS = 1024
SETS = 16
ROUNDS = 8
EXTENSION_PATH = (Path(__file__).parent / ".." / "target" / "release" / "libsqlite_instrument_rs.so").resolve()


def run_benchmark(query: str, setup_queries: list[str]):
    # Create bare connection
    bare_conn = sqlite3.connect("bench.db")

    # Create instrumented connection
    instrumented_conn = sqlite3.connect("bench.instrumented.db")
    instrumented_conn.enable_load_extension(True)
    instrumented_conn.load_extension(str(EXTENSION_PATH))

    def _run_queries():
        # Run setup queries if provided
        if setup_queries:
            for setup_query in setup_queries:
                bare_conn.execute(setup_query)
                instrumented_conn.execute(setup_query)
            bare_conn.commit()
            instrumented_conn.commit()

        bare_time = 0
        instrumented_time = 0
        count = 0

        for _ in range(ROUNDS):
            bare_time += min(repeat( lambda: bare_conn.execute(query), repeat=SETS, number=REPS))
            instrumented_time += min(repeat( lambda: instrumented_conn.execute(query), repeat=SETS, number=REPS))
            count += REPS

        # Report results
        print(f"\n#### `{query}`", '\n', '-' * 45, sep='')

        # Calculate per-query times
        bare_time_per_query_us = (bare_time / count) * 1_000_000
        instrumented_time_per_query_us = (instrumented_time / count) * 1_000_000
        overhead_per_query_us = instrumented_time_per_query_us - bare_time_per_query_us

        print(f"Time per bare query:\t\t{bare_time_per_query_us:.2f} μs")
        print(f"Time per instrumented query:\t{instrumented_time_per_query_us:.2f} μs")
        print(f"Overhead per query:\t\t{overhead_per_query_us:.2f} μs")
        print(f"Overhead percentage:\t\t{(overhead_per_query_us / bare_time_per_query_us * 100):.1f}%")
        print(f"Total queries:\t\t\t{count}")

        # Sanity check
        assert bare_time < instrumented_time, "Bare connection should be faster than instrumented"

    try:
        _run_queries()
    finally:
        bare_conn.close()
        instrumented_conn.close()

        for db_file in ["bench.db", "bench.instrumented.db", "bench.instrumented.trace.db"]:
            Path(db_file).unlink(missing_ok=True)



benchmarks = [
    # (STATEMENT: str, SETUP: list[str])
    ("SELECT 1", []),
    ("INSERT INTO test (value) VALUES (1)", ["CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)"]),
]


if __name__ == "__main__":
    print("SQLite Instrumentation Overhead Benchmark", '\n', "=" * 45, sep='')

    if not EXTENSION_PATH.exists():
        raise FileNotFoundError(
            f"SQLite extension not found at: {EXTENSION_PATH}\n"
            f"Run 'cargo build --release' first."
        )

    print(f"Using extension: {EXTENSION_PATH}")

    for query, setup_queries in benchmarks:
        run_benchmark(query, setup_queries)
