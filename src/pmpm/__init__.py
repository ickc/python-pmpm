"""pmpm—Python Manual Package Manager
"""

import logging
import os

try:
    from coloredlogs import ColoredFormatter as Formatter
except ImportError:
    from logging import Formatter

__version__ = "0.2.0"

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)
handler.setFormatter(Formatter("%(name)s %(levelname)s (%(module)-s): %(message)s"))
try:
    level = os.environ.get("PMPMLOGLEVEL", logging.INFO)
    logger.setLevel(level=level)
except ValueError:
    logger.setLevel(level=logging.INFO)
    logger.error("Unknown PMPMLOGLEVEL %s, set to default INFO.", level)
