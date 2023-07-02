from datetime import datetime
from logging import Formatter

from variables import tz

class NepalFormatter(Formatter):
    """
    Custom class for configuring timezone for logging to file
    """
    converter = lambda *args: datetime.now(tz).timetuple()