"""
Logger implementations for the coding experiments library.

This module provides concrete implementations of the TransmissionLogger
protocol for logging transmission events with different storage and
output strategies.

"""

from typing import List, Dict, Any
from .types import TransmissionLog, TransmissionLogger
import pandas as pd

# Module metadata
__author__ = "Mikhail Mikhailov"
__license__ = "MIT"
__version__ = "0.1.0"
__all__ = ["PlainLogger", "ConsoleLogger", "NullLogger"]


class PlainLogger(TransmissionLogger):
    """
    Simple logger that stores all log entries in memory.

    This logger maintains an in-memory list of all transmission logs,
    which can be accessed later for analysis or debugging.

    Attributes:
        logs: List of all logged TransmissionLog entries
    """

    def __init__(self) -> None:
        """
        Initialize an empty PlainLogger.
        """
        self.logs: List[TransmissionLog] = []
        """List of all logged transmission entries."""

    def log(self, log_entry: TransmissionLog) -> None:
        """
        Store a transmission log entry in memory.

        Args:
            log_entry: The transmission log entry to record
        """
        self.logs.append(log_entry)


class ConsoleLogger(TransmissionLogger):
    """
    Logger that prints log entries to the console.

    This logger outputs transmission events to standard output,
    making it useful for real-time monitoring and debugging.

    Attributes:
        verbose: If True, prints detailed log information;
                 if False, prints only summary information
    """

    def __init__(self, verbose: bool = True) -> None:
        """
        Initialize a ConsoleLogger.

        Args:
            verbose: Whether to print detailed log information
        """
        self.verbose = verbose
        """Verbosity setting for log output."""

    def log(self, log_entry: TransmissionLog) -> None:
        """
        Print a transmission log entry to the console.

        Args:
            log_entry: The transmission log entry to print
        """
        if self.verbose:
            print(
                f"[{log_entry.timestamp:.6f}] {log_entry.event.value}: "
                f"Message {log_entry.message.id}: {log_entry.message.data} // {log_entry.data}"
            )
        else:
            print(f"{log_entry.event.value}: Message {log_entry.message.id}")


class NullLogger(TransmissionLogger):
    """
    Logger that discards all log entries (no-op).

    This logger implements the TransmissionLogger protocol but
    performs no actual logging. It's useful for performance
    optimization when logging is not required.
    """

    def __init__(self) -> None:
        """
        Initialize a NullLogger.
        """
        pass

    def log(self, log_entry: TransmissionLog) -> None:
        """
        Discard a transmission log entry (no operation).

        Args:
            log_entry: The transmission log entry to discard
        """
        pass  # Intentionally does nothing

class PandasLogger(TransmissionLogger):
    """
    Logger that stores log entries in a pandas DataFrame.
    
    This logger maintains a DataFrame with all transmission logs,
    enabling easy analysis, filtering, and visualization using
    pandas operations.
    
    Attributes:
        df: DataFrame containing all logged entries
        _logs: Internal list of logs (for backward compatibility)
    """
    
    def __init__(self) -> None:
        """
        Initialize a PandasLogger.
        """
        self._logs: List[TransmissionLog] = []
        self.row_data : List[Dict[str, Any]] = []
    
    def log(self, log_entry: TransmissionLog) -> None:
        """
        Store a transmission log entry in a row list
        
        Args:
            log_entry: The transmission log entry to record
        """
        # Store in internal list for backward compatibility
        self._logs.append(log_entry)
        
        # Prepare data for DataFrame
        self.row_data.append({
            'timestamp': log_entry.timestamp,
            'event': log_entry.event.value,
            'message_id': log_entry.message.id,
            'message_data': ''.join(log_entry.message.data),
        })
   
    @property
    def dataframe(self) -> pd.DataFrame:
        """
        Get the log data as a pandas DataFrame.
        
        Returns:
            DataFrame containing all logged entries
        """
        return pd.DataFrame(self.row_data, columns = ['timestamp', 'event', 'message_id', 'message_data'])
    
    
