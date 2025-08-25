# SQLite Instrument Rust

A SQLite extension written in Rust that instruments database operations.

## What it does

Loads as a SQLite extension and creates a trace database along side the original database.

## Build

```bash
cargo build
```

Creates `target/debug/libsqlite_instrument_rs.so`

## Demo/Test

```bash
uv run test.py
```

This runs the Python test script that loads the extension into SQLite and verifies it works. The script uses Python 3.13 which has proper SQLite extension loading support.

## Requirements

- SQLite with extension support
