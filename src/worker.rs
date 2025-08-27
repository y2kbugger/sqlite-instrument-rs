//! Logging worker thread implementation
//!
//! Handles asynchronous logging of SQL trace data to files.

use std::fs::OpenOptions;
use std::io::{BufWriter, Write};
use std::sync::{mpsc, Mutex};
use std::thread::{self, JoinHandle};

/// Type aliases for cleaner interfaces
pub type LogSender = mpsc::Sender<LogMessage>;
pub type ThreadHandle = Mutex<Option<JoinHandle<()>>>;
pub type LoggingSystem = (LogSender, ThreadHandle);

/// Messages that can be sent to the logging worker thread
#[derive(Debug)]
pub enum LogMessage {
    Sql(String),
    Shutdown,
}

/// Initialize the logging worker system
/// Returns a sender that can be stored globally and a join handle for cleanup
pub fn initialize() -> LoggingSystem {
    let (tx, rx) = mpsc::channel::<LogMessage>();

    let handle = thread::Builder::new()
        .name("logging-worker".into())
        .spawn(move || {
            let file = OpenOptions::new()
                .create(true)
                .append(true)
                .open("testicall.log")
                .expect("Failed to open testicall.log");
            let mut writer = BufWriter::new(file);

            for message in rx.iter() {
                match message {
                    LogMessage::Sql(sql_text) => {
                        if let Err(e) = writeln!(writer, "{}", sql_text) {
                            eprintln!("Failed to write to log: {}", e);
                        }
                    }
                    LogMessage::Shutdown => {
                        // Flush and exit cleanly
                        let _ = writer.flush();
                        break;
                    }
                }
            }
        })
        .expect("Failed to spawn logging thread");

    (tx, Mutex::new(Some(handle)))
}
