import logging
import os
from enum import Enum, auto
import coloredlogs

class LoggingSource(Enum):
    MAIN = auto()
    COACH = auto()
    MCTS = auto()
    ARENA = auto()
    NN = auto()
    GAME = auto()

sources_to_log = {
    LoggingSource.MAIN: True,
    LoggingSource.COACH: True,
    LoggingSource.MCTS: True,
    LoggingSource.ARENA: True,
    LoggingSource.NN: True,
    LoggingSource.GAME: True,
}
    

class SplendorLogger:
    """
    Centralized logging utility for the Splendor AlphaZero implementation.
    This class provides a consistent interface for logging across all modules.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one logger instance exists"""
        if cls._instance is None:
            cls._instance = super(SplendorLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Initialize the logger with the specified parameters.
        
        Args:
            output_mode: Where to output logs (file, console, both, or none)
            log_file_path: Path to the log file (required if output_mode involves file)
            log_level: The logging level (INFO, DEBUG, etc.)
            verbose: Whether to enable verbose logging
        """
        if self._initialized:
            return
        
        self.log_file_path = None
        self.verbose = None
        
        self._initialized = True

    def configure(self, log_file_path, verbose):
        self.log_file_path = log_file_path
        self.verbose = verbose

        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
    def clear_logs(self):
        if self.log_file_path is None:
            raise ValueError("log_file_path is not set")
        with open(self.log_file_path, 'w') as f:
            f.write('')

    def log(self, message, source: LoggingSource, print_to_terminal=False):
        """
        Log a message with the configured logger.
        
        Args:
            message: The message to log
            print_to_terminal: Force print to terminal regardless of settings
        """
        if not self.verbose:
            return
        
        # Write to log file
        if self.log_file_path is not None:
            with open(self.log_file_path, 'a') as f:
                f.write(f"{message}\n")
        
        # Handle explicit terminal printing if requested
        if print_to_terminal:
            print(message)
    
    # def debug(self, message, module=None, print_to_terminal=False):
    #     """Log a debug message"""
    #     self.log(message, module, print_to_terminal, logging.DEBUG)
    
    # def info(self, message, module=None, print_to_terminal=False):
    #     """Log an info message"""
    #     self.log(message, module, print_to_terminal, logging.INFO)
    
    # def warning(self, message, module=None, print_to_terminal=False):
    #     """Log a warning message"""
    #     self.log(message, module, print_to_terminal, logging.WARNING)
    
    # def error(self, message, module=None, print_to_terminal=False):
    #     """Log an error message"""
    #     self.log(message, module, print_to_terminal, logging.ERROR)
    
    # def critical(self, message, module=None, print_to_terminal=False):
    #     """Log a critical message"""
    #     self.log(message, module, print_to_terminal, logging.CRITICAL)
        
    def set_verbose(self, verbose):
        """Set the verbose flag"""
        self.verbose = verbose
        
    def clear_log_file(self):
        """Clear the contents of the log file"""
        if self.log_file_path and os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'w') as f:
                f.write('')
                
    # def create_new_log_file(self, folder="./logs", base_name=None):
    #     """
    #     Create a new log file with an automatically incrementing number.
        
    #     Args:
    #         folder: Directory where log files are stored
    #         base_name: Base name for the log file (without extension)
            
    #     Returns:
    #         The path to the newly created log file
    #     """
    #     os.makedirs(folder, exist_ok=True)
        
    #     # Find existing log files
    #     existing_files = [f for f in os.listdir(folder) if f.endswith('.txt')]
        
    #     # Get next index
    #     try:
    #         existing_indices = [int(f.split('.')[0]) for f in existing_files if f.split('.')[0].isdigit()]
    #         next_index = max(existing_indices, default=0) + 1
    #     except ValueError:
    #         next_index = 1
            
    #     # Create new file path
    #     if base_name:
    #         new_file_path = f"{folder}/{base_name}_{next_index}.txt"
    #     else:
    #         new_file_path = f"{folder}/{next_index}.txt"
            
    #     # Update logger configuration
    #     self.log_file_path = new_file_path
        
    #     # Reconfigure handlers if using file output
    #     if self.output_mode in [LoggingOutput.FILE, LoggingOutput.BOTH]:
    #         # Remove existing file handlers
    #         for handler in self.logger.handlers[:]:
    #             if isinstance(handler, logging.FileHandler):
    #                 self.logger.removeHandler(handler)
            
    #         # Add new file handler
    #         file_handler = logging.FileHandler(new_file_path, mode='a')
    #         file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #         file_handler.setFormatter(file_formatter)
    #         self.logger.addHandler(file_handler)
        
    #     return new_file_path


# Create a default instance
logger = SplendorLogger()