-- SQLite Instrumentation Tables
-- These tables store execution statistics and performance data

-- Table to track SQL execution counts by hash
CREATE TABLE IF NOT EXISTS _y2k__execution_counts (
    hash INTEGER PRIMARY KEY,     -- DJB2 hash of the SQL statement
    count INTEGER DEFAULT 0,      -- Number of times this SQL was executed
    sql_text TEXT                 -- The original SQL statement text
);

-- Table to log detailed execution profiles
CREATE TABLE IF NOT EXISTS _y2k__profile_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique log entry ID
    sql_hash INTEGER,                      -- DJB2 hash of the SQL statement
    sql_text TEXT,                         -- The original SQL statement text
    time_ns INTEGER,                       -- Timestamp when execution completed (nanoseconds)
    duration_ns INTEGER,                   -- Execution duration (nanoseconds)
    autocommit_status INTEGER,             -- SQLite autocommit status (0=OFF, 1=ON)
    txn_state INTEGER                      -- Transaction state (0=NONE, 1=READ, 2=WRITE)
);
