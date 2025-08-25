import sqlite3



def test_instrumentation_tables_created(cursor: sqlite3.Cursor):
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE '_y2k__%'
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]

    expected_tables = {"_y2k__execution_counts", "_y2k__profile_log"}

    assert set(tables) == expected_tables, f"Expected tables {expected_tables}, but got {tables}"
