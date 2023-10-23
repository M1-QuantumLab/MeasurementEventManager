'''
Instrument server wrapper for pyHegel by Christian Lupien (Universite de
Sherbrooke).

Requires the pyHegel module to be installed; contact Christian for a copy.
'''

import os

import yaml

import pyHegel.commands as ph_cmd
import pyHegel.instruments as instruments

from measurement_event_manager.server_plugins.base import BaseServer


###############################################################################
## pyHegel server class
###############################################################################


class PyHegelServer(BaseServer):


    def __init__(self, config_path, **kwargs):
        ## Define attributes we will need later
        self._config_path = os.path.abspath(config_path)
        self._config = None
        ## Call the base class constructor
        super(PyHegelServer, self).__init__(**kwargs)


    def setup(self):
        '''Set up the pyHegel instrument registry according to the config
        '''
        ## Load config
        self.logger.info('Loading config from {}'.format(self._config_path))
        with open(self._config_path, 'r') as config_file:
            self._config = yaml.safe_load(config_file)
        self.logger.debug('Instrument config loaded from file.')
        ## Set up instruments with args in config (addresses, etc.)
        for instr_name, instr_dict in self._config.items():
            ## The driver name is the key, the value is a list of args
            driver_name = instr_dict.keys()[0]
            driver_args = instr_dict[driver_name]
            ## Initialize the instrument with the corresponding driver
            self.logger.info('Initializing {} with driver {}'\
                             .format(instr_name, driver_name))
            self.logger.info('{}'.format(driver_args))
            instr = getattr(instruments, driver_name)(*driver_args)
            self.logger.debug('Instrument created; registering...')
            ## Name fix from alexis - this might work to register the name properly
            instr.header.set(instr_name)
            ## Register the instrument with the global pyHegel namespace
            ph_cmd._globaldict[instr_name] = instr
            self.logger.info('Instrument registered.')


    def preset(self, params):
        '''Preset single-value instrument parameters before the sweep starts
        '''
        ## Iterate over instruments in the setvals
        for instr_name, instr_setvals in params.setvals.items():
            ## Get the instrument object
            instr = ph_cmd._globaldict[instr_name]
            self.logger.debug('Presetting values for {}'.format(instr))
            ## Iterate over the devices for each parameter
            for device_name, new_value in instr_setvals.items():
                ## Execute the set function on the corresponding parameter
                getattr(instr, device_name).set(new_value)
                self.logger.debug('{} set to {}'.format(device_name,
                                                        new_value))


    def measure(self, params):
        '''Carry out the measurement using pyHegel sweep
        '''
        
        ## Get the sweep device
        sweep_instr = ph_cmd._globaldict[params.sweep['instrument']]
        sweep_device = getattr(sweep_instr, params.sweep['device'])
        
        ## Get sweep values
        sweep_type = params.sweep.get('sweep_type', 'lin')
        sweep_value_kwargs = {}
        if sweep_type == 'lin':
            sweep_value_kwargs['start'] = params.sweep['start_value']
            sweep_value_kwargs['stop'] = params.sweep['stop_value']
            sweep_value_kwargs['npts'] = params.sweep['n_pts']
            sweep_value_kwargs['logspace'] = False
        ## TODO implement logspace and custom value specification
        else:
            raise ValueError('sweep_type must be one of: {}'.format(
                ['lin',]
                ))

        ## Get the output device
        output_instr = ph_cmd._globaldict[params.output['instrument']]
        output_device = getattr(output_instr, params.output['device'])
        
        ## Call pyHegel sweep
        ph_cmd.sweep(dev=sweep_device,
                     out=output_device,
                     filename='ph_big_test.txt',
                     **sweep_value_kwargs)
