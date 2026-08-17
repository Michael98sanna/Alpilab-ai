"""Cloud-side access to Alpilab Hub.

The Hub process itself lives in the `hub` package (future Windows service).
This module is the backend integration boundary.
"""

from hub.interface import AlpilabHub
from hub.mock import MockAlpilabHub

__all__ = ["AlpilabHub", "MockAlpilabHub"]
