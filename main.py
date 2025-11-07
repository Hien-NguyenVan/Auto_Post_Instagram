import os
import logging
from core.app import App
from config import LOG_DIR, LOG_FILE, LOG_FORMAT, LOG_LEVEL


def setup_logging():
    """
    Setup logging configuration for the application.

    Logs to both file and console with proper formatting.
    """
    # Create logs directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # Log startup
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Application started")
    logger.info("=" * 60)


if __name__ == "__main__":
    setup_logging()
    app = App()
    app.mainloop()
