import logging
import os

from pythonjsonlogger import jsonlogger


def setup_logging(app):
    level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logger = logging.getLogger()
    logger.setLevel(level)

    logger.handlers.clear()
    handler = logging.StreamHandler()
    fmt = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    app.logger.info('App demarree', extra={'service': 'devportfolio'})
