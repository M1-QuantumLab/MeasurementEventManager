"""
Instrument server wrapper for pyHegel by Christian Lupien (Université de
Sherbrooke).

Requires the pyHegel module to be installed; contact Christian for a copy.
"""

from collections.abc import Mapping
import os
import time

import pyHegel.commands as ph_cmd
import pyHegel.instruments as instruments

from ..measurement import Measurement
from .base import BaseServer


###############################################################################
## pyHegel server class
###############################################################################


class PyHegelServer(BaseServer):
    """An instrument server plugin for pyHegel
    """


    def setup(self, instrument_config: Mapping) -> None:

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


    def preset(self, params: Measurement) -> None:

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


    def measure(self, params: Measurement) -> str:

        ## Get the output device(s)
        output_device_list = []
        if "channels" not in params.output:
            self.logger.error("No output channels are defined!")
        for channel_dict in params.output["channels"]:
            output_instr = ph_cmd._globaldict[channel_dict['instrument']]
            output_device = getattr(output_instr, channel_dict['device'])
            ## We have the opportunity to do some more specifications here if
            ## need be, eg by wrapping or some other tricks.
            ## For now, we'll just use the device directly.
            output_device_list.append(output_device)

        ## Construct the target file path
        ## Get the file name and directory
        target_filename = params.output.get('filename', 'default.txt')
        data_dir = params.output.get('data_dir', None)
        ## Make sure the directory exists (otherwise pyHegel fails)
        if not os.path.exists(data_dir):
            self.logger.debug(f'Creating dirs: {data_dir}')
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

            ## When sweeping, we can pass the list of output devices directly
            output_devices = output_device_list

            sweep_devices = []
            sweep_kwargs_list = []

            ## Iterate over sweep dimensions (dicts in a list)
            for sweep_dim in params.sweep:

                ## Start with defaults so we can guarantee presence of keys
                sweep_kwargs = {
                    "stop": None,
                    "npts": None,
                    "logspace": False,
                    "reset": False,
                    "close_after": False,
                    "first_wait": None,
                    "beforewait": None,
                }

                ## Check if it is a fully-fledged instrument we want to sweep, or
                ## instead a logical device (eg a SweepDevice wrapper)
                if 'instrument' in sweep_dim:
                    sweep_instr = ph_cmd._globaldict[sweep_dim['instrument']]
                    sweep_device = getattr(sweep_instr, sweep_dim['device'])
                else:
                    sweep_device = ph_cmd._globaldict[sweep_dim['device']]
                ## Consolidate
                sweep_devices.append(sweep_device)

                ## Get sweep values
                sweep_type = sweep_dim.get('sweep_type', 'lin')
                if sweep_type == 'lin':
                    sweep_kwargs['start'] = sweep_dim['start_value']
                    sweep_kwargs['stop'] = sweep_dim['stop_value']
                    sweep_kwargs['npts'] = sweep_dim['n_pts']
                    sweep_kwargs['logspace'] = False
                ## TODO implement logspace and custom value specification
                elif sweep_type == 'list':
                    sweep_kwargs['start'] = sweep_dim['values']
                else:
                    raise ValueError('sweep_type must be one of: {}'.format(
                        ['lin',]
                        ))
                ## Additional sweep parameters
                sweep_kwargs['beforewait'] = sweep_dim.get('wait', 0.0)

                ## Consolidate
                sweep_kwargs_list.append(sweep_kwargs)

            ## Call pyHegel sweep
            ## Single sweep
            if len(params.sweep) == 1:
                ## Here we don't bother with the containers to keep it simple
                ph_cmd.sweep(
                    dev=sweep_device,
                    out=output_devices,
                    filename=target_path,
                    extra_conf=extras_list,
                    **sweep_kwargs,
                )
            ## MultiSweep
            else:
                ## Arrange kwargs correctly
                multisweep_kwargs = {
                    kk: [dd[kk] for dd in sweep_kwargs_list]
                    for kk in sweep_kwargs_list[0]
                }

                ## Call multisweep
                ph_cmd.sweep_multi(
                    dev=sweep_devices,
                    out=output_devices,
                    filename=target_path,
                    extra_conf=extras_list,
                    **multisweep_kwargs,
                )

        ## Not sweeping - just a single call to get (eg a single VNA trace)
        else:

            ## When not sweeping, we need to be more careful about the handling
            ## of single vs multiple outputs (pyHegel quirks, apparently).
            ## If there is only a single output device, we pass it in by itself
            if len(output_device_list) == 1:
                output_devices = output_device_list[0]
            else:
                ## I cannot figure out how to get multiple output channels to
                ## work in a straight get() call with no sweeps.
                raise NotImplementedError(
                    "It is unclear at this time how to handle multiple output "
                    "channels in an unswept call to get()."
                )
                # output_devices = tuple(output_device_list)

            ph_cmd.get(
                dev=output_devices,
                filename=target_path,
                extra_conf=extras_list,
            )

        ## Pass the output file path back to the caller for config dump,
        ## database collation at the Listener, etc.
        return target_path
