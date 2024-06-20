import logging

from app.core.config import settings


def create_logger():
    """
    Setup the logging environment
    """
    log = logging.getLogger(__name__)  # root logger
    log.setLevel(logging.DEBUG)
    format_str = "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s - %(funcName)s() ] - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(format_str, date_format)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    log.addHandler(handler)

    log.propagate = False

    my_adapter = logging.LoggerAdapter(log, {"tag": settings.APPLICATION_NAME})

    return my_adapter


log = create_logger()
