# SQLite Instrument Rust

A SQLite extension written in Rust that instruments a database for production-time observability.

Trace and monitor query execution and performance metrics in real time. This data can be leveraged for debugging, performance analysis, and real-time monitoring.

With a latency overhead of less than 1 microsecond (thats μs not ms), sqlite-instrument-rs is light you don't have to worry about slowing things down.


# Quick Start
Load the extension into SQLite at the sqlite3 command line:

```sql
.load 'target/release/libsqlite_instrument_rs'
```

or in say, python,

```python
import sqlite3
conn = sqlite3.connect('my.db')
conn.enable_load_extension(True)
conn.load_extension('target/release/libsqlite_instrument_rs.so')
```

Then traces will be stored in `my.trace.db`

## Requirements
- SQLite with extension support
- Access to the filesystem to create a new trace database

# Dev

For development commands, see:

    make

This will show all available build, test, and benchmark targets.

    $ make
    help:      Show this help.
    build:     Build debug version of the extension
    test:      Run pytest test suite
    bench:     Run performance benchmarks
    release:   Build release version of the extension

## Testing
Tests are written in python using `pytest`. To run the tests, execute:

    $ make test

they are located in the `tests` directory.
