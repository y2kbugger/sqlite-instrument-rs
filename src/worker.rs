//! Logging worker thread implementation
//!
//! Handles asynchronous logging of SQL trace data to files.

use std::fs::OpenOptions;
use std::io::Write;
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

    let handle = thread::spawn(move || {
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open("testicall.log")
            .expect("Failed to open testicall.log");

        while let Ok(message) = rx.recv() {
            match message {
                LogMessage::Sql(sql_text) => {
                    if let Err(e) = writeln!(file, "{}", sql_text) {
                        eprintln!("Failed to write to log: {}", e);
                    }
                    if let Err(e) = file.flush() {
                        eprintln!("Failed to flush log: {}", e);
                    }
                }
                LogMessage::Shutdown => {
                    // Flush and exit cleanly
                    let _ = file.flush();
                    break;
                }
            }
        }
    });

    (tx, Mutex::new(Some(handle)))
}
