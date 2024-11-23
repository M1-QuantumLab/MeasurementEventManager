"""
Controller/measurement messaging interfaces

These interfaces provide communication between the EventManager and Controller
instances, according to the MEM-MS protocol specification.
"""

import json

from measurement_event_manager.util.errors import (
    ServerError,
    HeaderError,
)
from ..measurement import Measurement, from_json
from .generic import (
    RequestInterface,
    ReplyInterface,
)


###############################################################################
## Measurement controller protocol REQ and REP interfaces
###############################################################################


## Controller client REQ interface
##################################


class ControllerRequestInterface(RequestInterface):
    """An interface for requests in the Controller REQ-REP pattern

    This interface should be associated with the spawned Controller process,
    which requests measurement definitions and provides status updates to the
    EventManager service.
    """


    def config(self) -> dict:
        """Get the instrument server config

        Returns:
            The instrument server config.

        Raises:
            HeaderError: Reply header does not match the request header
            ServerError: The server experienced an unspecified error
        """

        ## Send request based on header and body
        reply_dict = self._send_request(header='CFG')
        ## Parse reply
        if reply_dict['header'] == 'CFG':
            ## Decode JSON to config dict
            config_dict = json.loads(reply_dict['body'][0])
            return config_dict
        elif reply_dict['header'] == 'ERR':
            raise ServerError(reply_dict['body'])
        else:
            raise HeaderError(reply_dict['header'])


    def next(self) -> Measurement:
        """Get the definition of the next measurement to be run

        Returns:
            The specification of the currently-active measurement.

        Raises:
            HeaderError: Reply header does not match the request header
            ServerError: The server experienced an unspecified error
        """

        ## Send request based on header and body
        reply_dict = self._send_request(header='NXT')
        ## Parse reply
        if reply_dict['header'] == 'NXT':
            ## Convert to a MeasurementParams object
            params = from_json(reply_dict['body'][0])
            return params
        elif reply_dict['header'] == 'ERR':
            raise ServerError(reply_dict['body'])
        else:
            raise HeaderError(reply_dict['header'])


    def start(self) -> bool:
        """Declare the start of the current measurement to the server

        Returns:
            True if the measurement start is accepted by the server.

        Raises:
            HeaderError: Reply header does not match the request header
            ServerError: The server experienced an unspecified error
        """

        ## Send request based on header and body
        reply_dict = self._send_request(header='STA')
        ## Parse reply
        if reply_dict['header'] == 'STA':
            return True
        elif reply_dict['header'] == 'ERR':
            raise ServerError(reply_dict['body'])
        else:
            raise HeaderError(reply_dict['header'])


    def end(self, params: Measurement) -> bool:
        """Declare the end of the current measurement to the server

        Args:
            params: The completed measurement definition.

        Returns:
            True if the measurement end is accepted by the server.

        Raises:
            HeaderError: Reply header does not match the request header
            ServerError: The server experienced an unspecified error
        """

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
    """An interface for replies in the Controller REQ-REP pattern

    This interface should be associated with the EventManager service,
    providing requested measurement definitions and receiving status updates
    from the spawned Controller process.
    """


    def process_request(self) -> None:
        """Process a received request

        When called, process the next request message in the queue from the
        Controller.
        The actual actions taken depend on the type of request, ie. the message
        header.

        Unrecognized but structurally-valid messsages will not raise an error,
        but will instead result in a reply with an error header.
        """

        ## Receive request
        request_dict = self._receive_request()
        protocol = request_dict['protocol']
        header = request_dict['header']
        body = request_dict['body']

        ## Placeholder to allow multi-part response body
        response_body = []

        ## Process request based on header

        if header == 'CFG':
            config = self._server.get_config()
            if config is not None:
                response_header = 'CFG'
                response_body.append(json.dumps(config))
            else:
                response_header = 'ERR'
                response_body.append('No instrument config is set')

        elif header == 'NXT':
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

