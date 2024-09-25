"""
A do-nearly-nothing instrument server plugin
"""

import time

from measurement_event_manager.measurement_params import MeasurementParams
from .base import BaseServer


###############################################################################
## Definitions and constants
###############################################################################


TOTAL_SLEEP_TIME = 6


###############################################################################
## Sleeper server class
###############################################################################


class SleeperServer(BaseServer):
    """A do-nearly-nothing instrument server plugin

    Intended for testing the workflow and/or debugging the MEM ecosystem.
    Does not require an actual instrument server application to function.
    """


    def preset(self, params: MeasurementParams) -> None:

        ## Log parameter values
        self._log_params(params)


    def measure(self, params: MeasurementParams) -> str:

        ## Wait
        self.logger.info('Starting imitation measurement')
        for ii in range(TOTAL_SLEEP_TIME):
            self.logger.info('Imitation measurement tick {}'.format(ii))
            time.sleep(1)
        self.logger.info('Imitation measurement completed.')
        return ""


    def _log_params(self, params: MeasurementParams) -> None:
        """Log the parameters stored in the measurement definition

        Args:
            params: The measurement definition
        """

        ## Defined here so we can change it easily if we need to
        write_fn = self.logger.info

        write_fn('### Measurement params ###')
        write_fn('Submitter: {}'.format(params.submitter))

        write_fn('+++ Metadata: +++')
        for key, value in params.metadata.items():
            write_fn('    {}: {}'.format(key, value))

        write_fn('+++ Output: +++')
        for key, value in params.output.items():
            write_fn('    {}: {}'.format(key, value))

        write_fn('+++ Setvals: +++')
        for instr_alias, instr_vals in params.setvals.items():
            write_fn(' -> {}'.format(instr_alias))
            for key, value in instr_vals.items():
                write_fn('    {}: {}'.format(key, value))

        write_fn('##########################')
