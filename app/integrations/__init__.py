"""External system integrations.

Integrations talk to other products only through explicit contracts.
Never import internal code from Alpilab Check or third-party tools.
"""

from app.integrations.alpilab_check import (
    AlpilabCheckConnector,
    MockAlpilabCheckConnector,
)

__all__ = ["AlpilabCheckConnector", "MockAlpilabCheckConnector"]
