//! SQLite Instrumentation Extension
//!
//! A Rust-based SQLite extension that instruments database operations
//! to collect execution statistics and performance data.

use rusqlite::ffi;
use rusqlite::{Connection, Result};

use std::os::raw::{c_char, c_int};

/// Entry point for SQLite to load the extension.
/// See <https://sqlite.org/c3ref/load_extension.html> on this function's name and usage.
/// # Safety
/// This function is called by SQLite and must be safe to call.
/// https://github.com/rusqlite/rusqlite/blob/master/examples/loadable_extension.rs
#[allow(clippy::not_unsafe_ptr_arg_deref)]
#[no_mangle]
pub unsafe extern "C" fn sqlite3_extension_init(
    db: *mut ffi::sqlite3,
    pz_err_msg: *mut *mut c_char,
    p_api: *mut ffi::sqlite3_api_routines,
) -> c_int {
    Connection::extension_init2(db, pz_err_msg, p_api, extension_init)
}

/// Initialize the instrumentation extension
fn extension_init(conn: Connection) -> Result<bool> {
    rusqlite::trace::log(
        ffi::SQLITE_WARNING,
        "Initializing SQLite Instrumentation Extension",
    );

    // Embed SQL schema from file at compile time
    let schema_sql = include_str!("../schema.sql");

    // Create instrumentation tables
    create_instrumentation_tables(&conn, schema_sql)?;

    // TODO: Set up tracing callbacks here
    // This would involve registering trace callbacks for SQLITE_TRACE_STMT and SQLITE_TRACE_PROFILE

    rusqlite::trace::log(
        ffi::SQLITE_WARNING,
        "SQLite Instrumentation Extension initialized successfully",
    );
    Ok(false) // Don't register permanently
}

/// Create the instrumentation tables from the schema SQL
fn create_instrumentation_tables(conn: &Connection, schema_sql: &str) -> Result<()> {
    // Execute each SQL statement in the schema
    for statement in schema_sql.split(';') {
        // Remove comment lines and clean up the statement
        let cleaned_statement = statement
            .lines()
            .filter(|line| !line.trim().starts_with("--") && !line.trim().is_empty())
            .collect::<Vec<_>>()
            .join("\n")
            .trim()
            .to_string();

        if !cleaned_statement.is_empty() {
            conn.execute(&cleaned_statement, [])?;
        }
    }

    // Verify both expected tables were created
    let expected_tables = ["_y2k__execution_counts", "_y2k__profile_log"];
    let query = format!(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ({})",
        (0..expected_tables.len())
            .map(|_| "?")
            .collect::<Vec<_>>()
            .join(", ")
    );

    let table_count: i32 = conn.query_row(&query, expected_tables, |row| row.get(0))?;

    if table_count == expected_tables.len() as i32 {
        rusqlite::trace::log(ffi::SQLITE_WARNING, "Created both instrumentation tables");
    } else {
        let message = format!(
            "Warning: Only created {} of {} expected tables",
            table_count,
            expected_tables.len()
        );
        rusqlite::trace::log(ffi::SQLITE_WARNING, &message);
    }

    Ok(())
}
