from measurement_event_manager.interfaces.generic import (
    RequestInterface,
    ReplyInterface,
)


###############################################################################
## Measurement controller protocol REQ and REP interfaces
###############################################################################


class ControllerRequestInterface(RequestInterface):


    pass


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

        if header == 'REQ':
            response_header = 'REQ'
            mp_json = self._server.get_current_measurement_json()
            response_body.append(mp_json)

        elif header == 'START':
            response_header = 'ACK'

        elif header == 'END':
            response_header = 'ACK'
            self._server.measurement_finished(body[0])

        ## More possible requests go here

        else:
            self.logger.error('Unknown request header {}'.format(header))
            response_header = 'ERR'
            response_body.append('Unknown request header {}'.format(header))

        ## Send reply
        self._send_reply(response_header, response_body)

