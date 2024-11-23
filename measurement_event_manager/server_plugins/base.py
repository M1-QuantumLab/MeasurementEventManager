"""
Abstract base class for instrument server plugins

The server plugins act as translation layers between the (relatively-)
standardized measurement specifications of the MEM ecosystem, and the specific
structures and data formats of the user-selected instrument communications
software.

Here, the base class BaseServer is provided, which should be inherited from
for the user's custom plugin for specific software.
"""

from collections.abc import Mapping
import logging
from typing import Optional

from measurement_event_manager.measurement_params import MeasurementParams


###############################################################################

class BaseServer:
    """Abstract base class for instrument server plugins
    """


    def __init__(self, logger: logging.Logger):
        """
        Args:
            logger: A logging object
        """

        self.logger = logger
        ## TODO make the plugin logger a child of the main Controller logger


    ## The following methods must be overridden by subclasses


    def setup(self, instrument_config: Optional[Mapping]) -> None:
        """Set up driver connections to the specified instruments

        Args:
            instrument_config: Addresses and startup options for instrument
                drivers.
        """
        pass


    def preset(self, params: MeasurementParams) -> None:
        """Set all fixed instrument values before starting the measurement

        Args:
            params: The measurement definition
        """
        pass


    def measure(self, params: MeasurementParams) -> str:
        """Execute the measurement based on the passed-in parameters object

        Returns:
            The path to the output file created by the measurement.
        """
        ## This function is expected to return the full path to the output
        ## file created by the measurement
        return None

