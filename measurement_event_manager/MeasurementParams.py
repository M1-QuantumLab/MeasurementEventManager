'''
A class for packaging measurement metadata 
'''

import datetime
import json

###############################################################################
## Custom JSON encoder/decoder
###############################################################################


## Encoding (MP -> JSON)
########################


class _MPEncoder(json.JSONEncoder):
    '''Custom JSON encoder for MeasurementParams objects
    '''
    def default(self, obj):
        ## First, check if we have a datetime object
        if isinstance(obj, datetime.datetime):
            ## This will return the ISO-formatted string representation
            return obj.isoformat()
        
        ## Fall back on any available _json methods
        try:
            return obj._json()
        ## Otherwise just use the default behaviour from the default encoder
        except AttributeError:
            return json.JSONEncoder.default(self, obj)


## Decoding (JSON -> MP)
########################

ISO_STRPTIME = '%Y-%m-%dT%H:%M:%S.%f'

def _mp_from_json(json_dict):
    '''object hook function for json.loads; use from_json() as a user!
    '''
    ## Handle the whole MeasurementParams object at the top level
    if 'MeasurementParams' in json_dict:
        mp_dict = json_dict['MeasurementParams']
        ## Pull out the start and stop times
        ## If they are present, we need to parse them back into datetime
        start_time = mp_dict.pop('start_time', None)
        if start_time is not None:
            start_time = datetime.datetime.strptime(start_time, ISO_STRPTIME)
        stop_time = mp_dict.pop('stop_time', None)
        if stop_time is not None:
            stop_time = datetime.datetime.strptime(stop_time, ISO_STRPTIME)
        ## Create the object
        mp_obj = MeasurementParams(**mp_dict)
        ## Set the start and stop times
        ## Calling the function with a None argument sets it to the current
        ## time, so we want to avoid setting a time that's not real
        ## There is probably a better way of doing this...
        if start_time is not None:
            mp_obj.set_start_time(start_time)
        if stop_time is not None:
            mp_obj.set_stop_time(stop_time)
        ## Return the final object with updated special params
        return mp_obj
    ## Handle any individual objects that require special parsing
    for key, value in json_dict.items():
        pass

    return json_dict


def from_json(json_object):
    '''Construct a MeasurementParams instance from a JSON object
    '''
    return json.loads(json_object, object_hook=_mp_from_json)


###############################################################################
## MeasurementParams class definition
###############################################################################


class MeasurementParams(object):

    def __init__(self,
                 measurement_type="default",
                 setvals=None,
                 ):

        ## Measurement type descriptor
        self.measurement_type = measurement_type

        ## Start and end datetime markers - begin uninitialized
        self.start_time = None
        self.stop_time = None

        ## Instrument parameters (measurement 'inputs')
        ## Note that the arg default is None to prevent mutation of the default
        ## empty dict (https://stackoverflow.com/questions/1132941/least-astonishment-and-the-mutable-default-argument)
        if setvals is None:
            self.setvals = {}
        else:
            self.setvals = setvals

        ## TODO add more descriptive/optional parameters
        ## Should these be allowed to be user-defined?


    ## JSON serialization
    #####################


    ## Custom serialization method for encoding
    def _json(self):
        return {'MeasurementParams': self.__dict__}


    ## User-facing serialization method
    def to_json(self):
        '''Serialize the MeasurementParams object as JSON
        '''
        return json.dumps(self, cls=_MPEncoder)


    ## Printed representation
    #########################

    
    def __repr__(self):
        repr_string_list = ['MeasurementParams(']
        for key, value in self.__dict__.items():
            repr_string_list.append('{}={},'.format(key, repr(value)))
        repr_string_list.append(')')
        repr_string = ''.join(repr_string_list)
        return repr_string


    ## Measurement administration
    #############################


    def set_start_time(self, time=None):
        '''Indicate that the measurement has started
        '''
        if time is None:
            self.start_time = datetime.datetime.now()
        else:
            self.start_time = time


    def set_stop_time(self, time=None):
        '''Indicate that the measurement has stopped or completed
        '''
        if time is None:
            self.stop_time = datetime.datetime.now()
        else:
            self.stop_time = time
