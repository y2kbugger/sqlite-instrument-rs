# SQLite Instrument Rust

A SQLite extension written in Rust that instruments database operations.

## What it does

Loads as a SQLite extension and creates a trace database along side the original database.

# Quick Start
Load the extension into SQLite at the sqlite3 command line:

```sql
.load target/release/libsqlite_instrument_rs.so
```

or in python

```python
import sqlite3
conn = sqlite3.connect('my.db')
conn.enable_load_extension(True)
conn.load_extension('target/release/libsqlite_instrument_rs.so')
```

Then traces will be stored in `my.trace.db`

# Dev
## Build

  cargo build

Creates `target/debug/libsqlite_instrument_rs.so`

## Test

  uv run --directory test -- pytest

## Release

  cargo build --release

Creates `target/release/libsqlite_instrument_rs.so`

## Requirements

- SQLite with extension support
