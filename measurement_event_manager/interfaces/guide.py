from measurement_event_manager import MeasurementParams
from measurement_event_manager.interfaces.generic import (
    RequestInterface,
    ReplyInterface,
)
from measurement_event_manager.util.errors import (
    QueueEmptyError,
)


###############################################################################
## Guide protocol REQ and REP interfaces
###############################################################################


## Guide client REQ interface
#############################


class GuideRequestInterface(RequestInterface):


    pass


## Guide server REP interface
#############################


class GuideReplyInterface(ReplyInterface):


    def process_request(self):

        ## Receive request
        request_dict = self._receive_request()
        protocol = request_dict['protocol']
        header = request_dict['header']
        body = request_dict['body']

        ## Placeholder list to allow multi-part response body
        response_body = []

        ## Process request based on header

        if header == 'IDN':
            self.logger.info('IDN request received.')
            response_header = 'IDN'
            ## TODO write proper IDN info

        elif header == 'ADD':
            self.logger.info('ADD request received.')
            response_header = 'ADD'
            ## Convert JSON specs to MeasurementParams objects
            mp_list = [MeasurementParams.from_json(mm) for mm in body]
            ## Add to the measurement queue
            added_indices = self._server.add_to_queue(mp_list)
            ## Add the index to the response body
            response_body.extend(str(ii) for ii in added_indices)

        elif header == 'QUE':
            self.logger.info('QUE request received.')
            response_header = 'QUE'
            queue_list = self._server.get_queue_elements()
            for meas_item in queue_list:
                response_body.append(meas_item.to_json())

        elif header == 'LEN':
            self.logger.info('LEN request received.')
            response_header = 'LEN'
            response_body.append(str(self._server.get_queue_length()))

        elif header == 'RMV':
            self.logger.info('RMV request received.')
            index_list = []
            ## Convert received indices to int
            if body:
                for index in body:
                    try:
                        index_int = int(index)
                    except ValueError:
                        self.logger.error('{} could not be converted to an '
                                          'int'.format(index))
                        continue
                    else:
                        index_list.append(index_int)
            ## Remove values from queue
            try:
                removed_indices = self._server.remove_from_queue(index_list)
            except QueueEmptyError:
                self.logger.error('Attempting to remove items from empty '
                                  'queue')
                response_header = 'ERR'
                response_body.append('Queue is empty; cannot remove items.')
            else:
                response_header = 'RMV'
                response_body.extend(str(ii) for ii in removed_indices)

        elif header == 'FCH':
            self.logger.info('FCH request received')
            if body:
                ## A new value for the counter has been given
                try:
                    counter = int(body[0])
                except ValueError:
                    self.logger.error('{} could not be converted to an int'\
                                      .format(body[0]))
                    response_header = 'ERR'
                    response_body.append('Invalid value passed for fetch '
                                         'counter')
                else:
                    ## Set the new counter value
                    new_counter = self._server.set_fetch_counter(counter)
                    response_header = 'FCH'
                    response_body.append(str(new_counter))
            else:
                ## No parameters - this is a request for the value
                response_header = 'FCH'
                current_counter = self._server.get_fetch_counter()
                response_body.append(str(current_counter))

        ## More possible requests go here

        else:
            self.logger.error('Unknown request header {}'.format(header))
            response_header = 'ERR'
            response_body.append('Unknown request header {}'.format(header))

        ## Send reply
        self._send_reply(response_header, response_body)

