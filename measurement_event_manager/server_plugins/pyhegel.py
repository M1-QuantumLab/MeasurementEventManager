'''
Instrument server wrapper for pyHegel by Christian Lupien (Universite de
Sherbrooke).

Requires the pyHegel module to be installed; contact Christian for a copy.
'''

import os
import time

import yaml

import pyHegel.commands as ph_cmd
import pyHegel.instruments as instruments

from measurement_event_manager.server_plugins.base import BaseServer


###############################################################################
## pyHegel server class
###############################################################################


class PyHegelServer(BaseServer):


    def __init__(self, **kwargs):
        ## Call the base class constructor
        super(PyHegelServer, self).__init__(**kwargs)


    def setup(self, instrument_config):
        '''Set up the pyHegel instrument registry according to the config
        '''

        ## Set up instruments with args in config (addresses, etc.)
        self.logger.info('Setting up instruments...')
        for instr_name, instr_dict in instrument_config.items():
            ## If the instr_name begins with an underscore '_', it is a logical
            ## device wrapper and will be handled differently below.
            ## This is because the parent instrument (_LogicalInstrument)
            ## doesn't play nicely in the same way as a regular instrument
            if instr_name[0] == '_':
                self.logger.debug(
                    'Skipping {}, as it is a logical device'.format(instr_name)
                )
                continue
            ## The driver name is the key, the value is a list of args
            ## Convert (hopefully) single-key dict to list, as Py3 does not
            ## allow subscripting of dict keys
            driver_name = list(instr_dict.keys())[0]
            driver_args = instr_dict[driver_name]
            ## Initialize the instrument with the corresponding driver
            self.logger.info('Initializing {} with driver {}'\
                             .format(instr_name, driver_name))
            self.logger.info('{}'.format(driver_args))
            instr = getattr(instruments, driver_name)(*driver_args)
            self.logger.debug('Instrument created; registering...')
            ## Name fix from Alexis
            ## This allows us to register the name of the instrument
            instr.header.set(instr_name)
            ## Register the instrument with the global pyHegel namespace
            ph_cmd._globaldict[instr_name] = instr
            self.logger.info('Instrument registered.')

        ## Now we'll do the logical device wrappers
        self.logger.info('Setting up logical device wrappers...')
        for dev_name, dev_dict in instrument_config.items():
            ## Skip all legitimate instruments (they have already been handled)
            if dev_name[0] != '_':
                self.logger.debug(
                    'Skipping {}, as it is a genuine instrument'\
                    .format(dev_name)
                )
                continue
            ## The device name is the key, the value is a DICT of args
            ## We need to treat things like the basedev (which will be an
            ## object handle) differently from passed-in parameter values
            driver_name = list(dev_dict.keys())[0]
            driver_kwargs = dev_dict[driver_name]
            ## The special kwarg 'basedev' will be used to pass a
            ## device object, so we have to fetch the correct object
            ## first
            if 'basedev' in driver_kwargs:
                ## Parse the name, in the format instrument.device
                basedev_iname, basedev_dname = driver_kwargs['basedev']\
                                               .split('.')
                self.logger.info(
                    'Fetching the device {} from instrument {}'\
                    .format(basedev_dname, basedev_iname)
                )
                ## Fetch the instrument
                basedev_instr = ph_cmd._globaldict[basedev_iname]
                ## Fetch the device
                basedev_dev = getattr(basedev_instr, basedev_dname)
                ## Replace the string specification with the actual object
                driver_kwargs['basedev'] = basedev_dev
            ## Create and assign the device directly, rather than the parent
            ## instrument
            self.logger.info('Initializing {} with driver {}'\
                             .format(dev_name, driver_name))
            self.logger.info('{}'.format(driver_kwargs))
            dev = getattr(instruments, driver_name)(**driver_kwargs)
            ## The name fix doesn't work here...
            ## Register the device directly with the global pyHegel namespace
            ph_cmd._globaldict[dev_name] = dev
            self.logger.info("Logical device registered.")
        ## TODO at some point if we have multiple levels of wrapping, or if we
        ## need fancier capabilities, we will have to change the structure, but
        ## for now this should work!


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

        ## Get the output device
        output_instr = ph_cmd._globaldict[params.output['instrument']]
        output_device = getattr(output_instr, params.output['device'])

        ## Construct the target file path
        ## Get the file name and directory
        target_filename = params.output.get('filename', 'default.txt')
        data_dir = params.output.get('data_dir', None)
        ## Make sure the directory exists (otherwise pyHegel fails)
        if not os.path.exists(data_dir):
            self.logger.debug('Creating dirs: f{data_dir}')
            os.makedirs(data_dir)
        ## Put the path together
        full_path = os.path.join(data_dir, target_filename)
        ## Do the pyHegel substitution, so we have a fixed string which we
        ## can also use to associate a copy of the config with the
        ## measurement
        target_path, _ = ph_cmd._process_filename(
            full_path,
            now=time.time(),
        )

        ## Append the metadata from the config to the extra_conf to be
        ## included in the output file
        extras_list = [
            str(key)+':'+str(value)
            for key, value in params.metadata.items()
        ]

        ## Sweep is present in the config
        if params.sweep:
            ## Check if it is a fully-fledged instrument we want to sweep, or
            ## instead a logical device (eg a SweepDevice wrapper)
            if 'instrument' in params.sweep:
                sweep_instr = ph_cmd._globaldict[params.sweep['instrument']]
                sweep_device = getattr(sweep_instr, params.sweep['device'])
            else:
                sweep_device = ph_cmd._globaldict[params.sweep['device']]

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
            ## Additional sweep parameters
            sweep_value_kwargs['beforewait'] = params.sweep.get('wait', None)

            ## Call pyHegel sweep
            ph_cmd.sweep(
                dev=sweep_device,
                out=output_device,
                filename=target_path,
                extra_conf=extras_list,
                **sweep_value_kwargs
            )

        ## Not sweeping - just a single call to get (eg a single VNA trace)
        else:
            ph_cmd.get(
                dev=output_device,
                filename=target_path,
                extra_conf=extras_list,
            )

        ## Pass the output file path back to the caller for config dump,
        ## database collation at the Listener, etc.
        return target_path
