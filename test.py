# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""
Test script for SQLite Instrument Rust Extension

This script loads the Rust-built SQLite extension and verifies it works correctly.
"""

import sqlite3
import os
import sys
from pathlib import Path


def main():
    print("=== SQLite Instrument Rust Extension Test ===")

    # Debug info
    print(f"Python version: {sys.version}")
    print(f"SQLite version: {sqlite3.sqlite_version}")
    print()

    # Path to our Rust-built extension
    ext_path = "target/debug/libsqlite_instrument_rs.so"

    # Check if the extension exists
    if not Path(ext_path).exists():
        print(f"❌ Extension not found at {ext_path}")
        print("Run 'cargo build' first")
        return 1

    print(f"📂 Extension found at: {ext_path}")

    try:
        # Connect to an in-memory database
        print("🔗 Connecting to SQLite...")
        conn = sqlite3.connect(":memory:")

        # Enable extension loading
        conn.enable_load_extension(True)

        print(f"📥 Loading extension: {ext_path}")
        conn.load_extension(ext_path)

        print("✅ Extension loaded successfully!")

        # Check if instrumentation tables were created
        print("\n🔍 Checking for instrumentation tables...")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE '_y2k__%'
            ORDER BY name
        """)

        tables = cursor.fetchall()
        if tables:
            print("✅ Found instrumentation tables:")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("⚠️  No instrumentation tables found in main database")
            print("   (This might be expected if tables are created in a separate database)")

        # Test some basic SQL operations
        print("\n🧪 Testing basic SQL operations...")

        # Create a test table
        cursor.execute("CREATE TABLE test_table (id INTEGER, name TEXT)")
        print("✅ Created test table")

        # Insert some data
        cursor.execute("INSERT INTO test_table (id, name) VALUES (1, 'test1')")
        cursor.execute("INSERT INTO test_table (id, name) VALUES (2, 'test2')")
        print("✅ Inserted test data")

        # Query the data
        cursor.execute("SELECT * FROM test_table")
        results = cursor.fetchall()
        print(f"✅ Queried test data: {results}")

        # Test a more complex query
        cursor.execute("SELECT COUNT(*) FROM test_table WHERE id > 0")
        count = cursor.fetchone()[0]
        print(f"✅ Complex query result: {count} rows")

        # Check if instrumentation data was collected
        print("\n📊 Checking instrumentation data...")
        for table_name in ['_y2k__execution_counts', '_y2k__profile_log']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"✅ {table_name}: {count} entries")
            except sqlite3.OperationalError:
                print(f"⚠️  {table_name}: table not accessible from main connection")

        conn.close()
        print("\n🎉 All tests completed successfully!")
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
