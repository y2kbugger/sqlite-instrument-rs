import ctypes

#######################################################
# Try to get the SQLite library - common names on Linux
try:
    # First try to get from the module itself
    sqlite_lib = ctypes.CDLL("libsqlite3.so.0")
except OSError:
    try:
        sqlite_lib = ctypes.CDLL("libsqlite3.so")
    except OSError:
        sqlite_lib = ctypes.CDLL("sqlite3")

# Define sqlite3_config function
sqlite3_config = sqlite_lib.sqlite3_config
sqlite3_config.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
sqlite3_config.restype = ctypes.c_int

# Define the error callback function type
ERROR_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p)

# SQLITE_CONFIG_LOG constant
SQLITE_CONFIG_LOG = 16

_current_log_callback = None
#######################################################


def enable_sqlite_error_log_capture() -> list[dict]:
    global _current_log_callback
    captured_logs = []

    def error_log_callback(pArg, iErrCode, zMsg):
        log_entry = {
            'error_code': iErrCode,
            'message': zMsg.decode('utf-8') if zMsg else "Unknown error"
        }
        captured_logs.append(log_entry)

    # Create the callback function
    _current_log_callback = ERROR_CALLBACK_TYPE(error_log_callback)

    # Set up the error logging callback
    _ = sqlite3_config(SQLITE_CONFIG_LOG, _current_log_callback, None)

    return captured_logs

def disable_sqlite_error_log_capture():
    _ = sqlite3_config(SQLITE_CONFIG_LOG, None, None)


class SqliteErrorLogCapture:
    """Context manager that captures SQLite logs and holds them internally"""

    def __init__(self):
        self.logs = []

    def __enter__(self):
        self.logs = enable_sqlite_error_log_capture()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        disable_sqlite_error_log_capture()
        return False

    def get_logs(self):
        return self.logs

    def get_messages(self):
        return [log['message'] for log in self.logs]

    def clear_logs(self):
        self.logs.clear()
