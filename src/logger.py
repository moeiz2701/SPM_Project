"""
Centralized logging configuration for Loyalty AI Agent
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class AgentLogger:
    """Centralized logger for the AI Agent system"""

    _instance: Optional[logging.Logger] = None

    @classmethod
    def get_logger(cls, name: str = "loyalty_agent", log_file: str = "logs/agent.log") -> logging.Logger:
        """
        Get or create logger instance

        Args:
            name: Logger name
            log_file: Path to log file

        Returns:
            Configured logger instance
        """
        if cls._instance is None:
            cls._instance = cls._setup_logger(name, log_file)
        return cls._instance

    @classmethod
    def _setup_logger(cls, name: str, log_file: str) -> logging.Logger:
        """
        Configure logger with file and console handlers

        Args:
            name: Logger name
            log_file: Path to log file

        Returns:
            Configured logger
        """
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # Avoid duplicate handlers
        if logger.handlers:
            return logger

        # Console handler (always works in serverless)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Try to add file handler (works locally, fails in serverless)
        try:
            # Use /tmp for serverless environments (only writable directory)
            import os
            if os.path.exists('/tmp') and os.access('/tmp', os.W_OK):
                log_file = '/tmp/agent.log'
            
            log_path = Path(log_file)
            log_path.parent.mkdir(exist_ok=True, parents=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # Silently fail file logging in read-only environments
            logger.info(f"File logging disabled (read-only filesystem): {e}")

        return logger


# Convenience function
def get_logger(name: str = "loyalty_agent") -> logging.Logger:
    """Get logger instance"""
    return AgentLogger.get_logger(name)
