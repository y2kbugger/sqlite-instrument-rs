//! SQLite Instrumentation Extension
//!
//! A Rust-based SQLite extension that instruments database operations
//! to collect execution statistics and performance data.

use rusqlite::ffi;
use rusqlite::trace::{TraceEvent, TraceEventCodes};
use rusqlite::Connection;
use thiserror::Error;

use std::os::raw::{c_char, c_int};
use std::path::Path;

#[derive(Debug, Error)]
pub enum SqliteInstrumentError {
    #[error("rusqlite error: {0}")]
    Sql(#[from] rusqlite::Error),
    #[error("`main` database not found")]
    MainNotFound,
}

type Result<T> = std::result::Result<T, SqliteInstrumentError>;

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
fn extension_init(conn: Connection) -> rusqlite::Result<bool> {
    rusqlite::trace::log(
        ffi::SQLITE_WARNING,
        "Initializing SQLite Instrumentation Extension",
    );

    // Get the main database file path
    let main_db_path = get_database_path(&conn).unwrap_or_default();

    // Create trace database path by appending .trace.db
    let trace_db_path = create_trace_db_path(&main_db_path);

    // Embed SQL schema from file at compile time
    let schema_sql = include_str!("../schema.sql");

    // Create instrumentation tables in separate trace database
    create_trace_database(&trace_db_path, schema_sql)?;

    // Set up tracev2 callback to log SQL statements and execution times
    conn.trace_v2(
        TraceEventCodes::SQLITE_TRACE_STMT | TraceEventCodes::SQLITE_TRACE_PROFILE,
        Some(|event| match event {
            TraceEvent::Stmt(stmt, sql) => {
                #[cfg(feature = "testing-logs")]
                {
                    let debug_message = format!("DEBUG: STMT traced - {}", sql);
                    rusqlite::trace::log(ffi::SQLITE_WARNING, &debug_message);
                }
                std::hint::black_box(stmt);
                std::hint::black_box(sql);
            }
            TraceEvent::Profile(stmt, duration) => {
                #[cfg(feature = "testing-logs")]
                {
                    let debug_message = format!("DEBUG: PROFILE traced - {}", stmt.sql());
                    rusqlite::trace::log(ffi::SQLITE_WARNING, &debug_message);
                }
                std::hint::black_box(stmt);
                std::hint::black_box(duration);
            }
            _ => {}
        }),
    );

    rusqlite::trace::log(
        ffi::SQLITE_WARNING,
        "SQLite Instrumentation Extension initialized successfully",
    );

    Ok(false) // Don't register permanently
}

/// Get the database file path using PRAGMA database_list
fn get_database_path(conn: &Connection) -> Result<String> {
    // this will always be the first database that a connection was opened with
    let mut stmt = conn.prepare("PRAGMA database_list")?;
    let rows = stmt.query_map([], |row| {
        let seq: i32 = row.get(0)?;
        let name: String = row.get(1)?;
        let file: Option<String> = row.get(2)?;
        Ok((seq, name, file))
    })?;

    for row in rows {
        let (seq, name, file) = row?;
        if name == "main" && seq == 0 {
            if let Some(file_path) = file {
                return Ok(file_path);
            } else {
                // In-memory database - use a temporary path
                return Ok(String::from(":memory:"));
            }
        }
    }

    Err(SqliteInstrumentError::MainNotFound)
}

/// Create trace database path by replacing or adding .trace.db suffix
fn create_trace_db_path(main_db_path: &str) -> String {
    let path = Path::new(main_db_path);

    let stem = path.file_stem().unwrap_or_default();
    let trace_filename = format!("{}.trace.db", stem.to_string_lossy());

    if let Some(parent) = path.parent() {
        parent.join(trace_filename).to_string_lossy().to_string()
    } else {
        trace_filename
    }
}

/// Create the trace database and instrumentation tables
fn create_trace_database(trace_db_path: &str, schema_sql: &str) -> rusqlite::Result<()> {
    let trace_conn = Connection::open(trace_db_path)?;

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
            trace_conn.execute(&cleaned_statement, [])?;
        }
    }

    // Verify expected tables were created
    let expected_tables = ["ExecutionCount", "Profile"];
    let query = format!(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ({})",
        (0..expected_tables.len())
            .map(|_| "?")
            .collect::<Vec<_>>()
            .join(", ")
    );

    let table_count: i32 = trace_conn.query_row(&query, expected_tables, |row| row.get(0))?;

    if table_count == expected_tables.len() as i32 {
        let message = format!("Created trace database: {}", trace_db_path);
        rusqlite::trace::log(ffi::SQLITE_WARNING, &message);
    } else {
        let message = format!(
            "Warning: Only created {} of {} expected tables in trace database",
            table_count,
            expected_tables.len()
        );
        rusqlite::trace::log(ffi::SQLITE_WARNING, &message);
    }

    Ok(())
}
