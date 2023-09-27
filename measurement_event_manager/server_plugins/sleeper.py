"""
The sleeper is a do-nearly-nothing instrument server that allows for 
dry-running the experiment flow and/or debugging the MEM ecosystem.
"""

import time

from measurement_event_manager.server_plugins.base import BaseServer


###############################################################################
## Definitions and constants
###############################################################################


TOTAL_SLEEP_TIME = 6


###############################################################################
## Sleeper server class
###############################################################################


class SleeperServer(BaseServer):


    def measure(self, params):
        '''Run an imitation measurement (log values and wait)
        '''

        ## Log parameter values
        self.log_params(params)

        ## Wait
        self.logger.info('Starting imitation measurement')
        for ii in range(TOTAL_SLEEP_TIME):
            self.logger.info('Imitation measurement tick {}'.format(ii))
            time.sleep(1)
        self.logger.info('Imitation measurement completed.')


    def log_params(self, params):
        '''Log the values of the settings in the MeasurementParams object
        '''

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

