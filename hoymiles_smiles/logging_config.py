"""Logging configuration with JSON format support."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from pythonjsonlogger import jsonlogger


class ContextFilter(logging.Filter):
    """Add contextual information to log records."""
    
    def __init__(self, context: Optional[dict] = None):
        """Initialize context filter.
        
        Args:
            context: Context dictionary to add to log records
        """
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to JSON log output."""
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields if not present
        if 'timestamp' not in log_record:
            log_record['timestamp'] = self.formatTime(record, self.datefmt)
        
        if 'level' not in log_record:
            log_record['level'] = record.levelname
        
        if 'logger' not in log_record:
            log_record['logger'] = record.name
        
        # Add exception info if present
        if record.exc_info and 'exc_info' not in log_record:
            log_record['exc_info'] = self.formatException(record.exc_info)


def setup_logging(
    level: str = "WARNING",
    format_type: str = "standard",
    log_file: Optional[Path] = None,
    console: bool = False,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    context: Optional[dict] = None,
) -> None:
    """Setup logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type (standard or json)
        log_file: Optional log file path
        console: Whether to log to console
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        context: Optional context to add to all log messages
    """
    # Convert level string to logging level
    log_level = getattr(logging, level.upper(), logging.WARNING)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if format_type == "json":
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Add context filter if provided
    if context:
        context_filter = ContextFilter(context)
        root_logger.addFilter(context_filter)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        try:
            # Ensure directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(log_file),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8',
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            root_logger.info(f"Logging to file: {log_file}")
            
        except Exception as e:
            root_logger.error(f"Failed to setup file logging: {e}")
    
    # Set specific loggers to appropriate levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('paho').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    root_logger.info(f"Logging configured: level={level}, format={format_type}, console={console}, file={log_file}")


def get_logger(name: str, context: Optional[dict] = None) -> logging.Logger:
    """Get a logger with optional context.
    
    Args:
        name: Logger name
        context: Optional context to add to log messages
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    if context:
        context_filter = ContextFilter(context)
        logger.addFilter(context_filter)
    
    return logger

