from measurement_event_manager import measurement_params
from measurement_event_manager.interfaces.generic import (
    RequestInterface,
    ReplyInterface,
)
from measurement_event_manager.util.errors import (
    ServerError,
    HeaderError,
)


###############################################################################
## Measurement controller protocol REQ and REP interfaces
###############################################################################


## Controller client REQ interface
##################################


class ControllerRequestInterface(RequestInterface):


    def next(self):
        '''Send a NXT request, returning the next measurement to be run
        '''
        ## Send request based on header and body
        reply_dict = self._send_request(header='NXT')
        ## Parse reply
        if reply_dict['header'] == 'NXT':
            ## Convert to a MeasurementParams object
            params = measurement_params.from_json(reply_dict['body'][0])
            return params
        elif reply_dict['header'] == 'ERR':
            raise ServerError(reply_dict['body'])
        else:
            raise HeaderError(reply_dict['header'])


    def start(self):
        '''Send a STA request, confirming measurement start
        '''
        ## Send request based on header and body
        reply_dict = self._send_request(header='STA')
        ## Parse reply
        if reply_dict['header'] == 'STA':
            return True
        elif reply_dict['header'] == 'ERR':
            raise ServerError(reply_dict['body'])
        else:
            raise HeaderError(reply_dict['header'])


    def end(self, params):
        '''Send an END request, indicating the measurement has completed
        '''
        ## Serialize the MeasurementParams object
        params_json = params.to_json()
        ## Send request based on header and body
        reply_dict = self._send_request(header='END', body=[params_json])
        ## Parse reply
        if reply_dict['header'] == 'END':
            return True
        elif reply_dict['header'] == 'ERR':
            raise ServerError(reply_dict['body'])
        else:
            raise HeaderError(reply_dict['header'])



## Controller server REP interface
##################################


class ControllerReplyInterface(ReplyInterface):


    def process_request(self):
        
        ## Receive request
        request_dict = self._receive_request()
        protocol = request_dict['protocol']
        header = request_dict['header']
        body = request_dict['body']

        ## Placeholder to allow multi-part response body
        response_body = []

        ## Process request based on header

        if header == 'NXT':
            response_header = 'NXT'
            mp_json = self._server.get_current_measurement_json()
            response_body.append(mp_json)

        elif header == 'STA':
            response_header = 'STA'

        elif header == 'END':
            response_header = 'END'
            self._server.measurement_finished(body[0])

        ## More possible requests go here

        else:
            self.logger.error('Unknown request header {}'.format(header))
            response_header = 'ERR'
            response_body.append('Unknown request header {}'.format(header))

        ## Send reply
        self._send_reply(response_header, response_body)

