"""
Guide messaging interfaces

These interfaces provide communication between a Guide service, the frontend of
the MEM ecosystem, and the EventManager service, according to the MEM-GD
protocol specification.
Customization of the Guide frontend can thus be carried out without requiring
a re-implementation of the messaging inteface, by using an instance of the GuideRequestInterface provided here as an attribute.
"""

from typing import Iterable, List

from measurement_event_manager import measurement_params
from measurement_event_manager.util.errors import (
    QueueEmptyError,
    ServerError,
    HeaderError,
)
from .generic import (
    RequestInterface,
    ReplyInterface,
)


###############################################################################
## Guide protocol REQ and REP interfaces
###############################################################################


## Guide client REQ interface
#############################


class GuideRequestInterface(RequestInterface):
    """An inteface for requests in the Guide REQ-REP pattern

    This interface should be associeted with the Guide process, converting API
    calls into messages sent to the EventManager service.
    The request messages include submitting measurement definitions, queue
    management, etc.
    """


    def add(self, params: measurement_params.MeasurementParams) -> List[int]:
        """Add a measurement definition to the queue

        Args:
            params: The submitted measurement definition.

        Returns:
            The queue index at which the measurement was added.

        Raises:
            HeaderError: Reply header does not match the request header
            ServerError: The server experienced an unspecified error
        """

        ## Serialize the MeasurementParams object
        params_json = params.to_json()
        ## Send request based on header and body
        reply_dict = self._send_request(header='ADD', body=[params_json])
        ## Make sure we haven't gotten an error
        ## TODO this should probably be packaged away somewhere
        if reply_dict['header'] == 'ADD':
            return reply_dict['body']
        elif reply_dict['header'] == 'ERR':
            raise ServerError(reply_dict['body'])
        else:
            raise HeaderError(reply_dict['header'])


    def query(self) -> List[measurement_params.MeasurementParams]:
        """Query the state of the queue

        Returns:
            The measurement definitions currently in the queue.

        Raises:
            HeaderError: Reply header does not match the request header
            ServerError: The server experienced an unspecified error
        """

        reply_dict = self._send_request(header='QUE')
        if reply_dict['header'] == 'QUE':
            queue_json = reply_dict['body']
            ## Convert to MeasurementParams objects
            queue_mp = [measurement_params.from_json(mp) for mp in queue_json]
            return queue_mp
        elif reply_dict['header'] == 'ERR':
            raise ServerError(reply_dict['body'])
        else:
            raise HeaderError(reply_dict['header'])


    def len(self) -> int:
        """Get the length of the queue

        Returns:
            The current length of the queue.

        Raises:
            HeaderError: Reply header does not match the request header
            ServerError: The server experienced an unspecified error
        """

        reply_dict = self._send_request(header='LEN')
        if reply_dict['header'] == 'LEN':
            return int(reply_dict['body'][0])
        elif reply_dict['header'] == 'ERR':
            raise ServerError(reply_dict['body'])
        else:
            raise HeaderError(reply_dict['header'])


    def remove(self, index_list: Iterable[int]) -> List[int]:
        """Remove measurements from the queue

        Items to remove are specified by index.
        Note that resolving syntactic sugar (eg slices) and ensuring the
        validity of the passed-in indices is the responsibility of the caller!

        Args:
            index_list: Nonnegative indices, convertible to strings
        
        Returns:
            The indices at which measurements were removed from the queue.

        Raises:
            HeaderError: Reply header does not match the request header
            ServerError: The server experienced an unspecified error
        """

        ## Ensure all indices are string type
        indices_str = [str(ii) for ii in index_list]
        ## Send request
        reply_dict = self._send_request(header='RMV', body=indices_str)
        if reply_dict['header'] == 'RMV':
            removed_indices_str = reply_dict['body']
            ## Convert str indices to numeric
            removed_indices = [int(ii) for ii in removed_indices_str]
            return removed_indices
        elif reply_dict['header'] == 'ERR':
            raise ServerError(reply_dict['body'])
        else:
            raise HeaderError(reply_dict['header'])


    def get_counter(self) -> int:
        """Check the state of the fetch counter

        Returns:
            The current value of the fetch counter.

        Raises:
            HeaderError: Reply header does not match the request header
            ServerError: The server experienced an unspecified error
        """

        reply_dict = self._send_request(header='FCH')
        if reply_dict['header'] == 'FCH':
            counter = int(reply_dict['body'][0])
            return counter
        elif reply_dict['header'] == 'ERR':
            raise ServerError(reply_dict['body'])
        else:
            raise HeaderError(reply_dict['header'])


    def set_counter(self, value: int) -> int:
        """Specify a new value for the fetch counter

        Args:
            value: The new value for the fetch counter.

        Returns:
            The value of the fetch counter after setting.

        Raises:
            HeaderError: Reply header does not match the request header
            ServerError: The server experienced an unspecified error
        """

        ## Convert the new value to a str and pack in a list
        value_msg = [str(value)]
        ## Send request
        reply_dict = self._send_request(header='FCH', body=value_msg)
        if reply_dict['header'] == 'FCH':
            counter = int(reply_dict['body'][0])
            return counter
        elif reply_dict['header'] == 'ERR':
            raise ServerError(reply_dict['body'])
        else:
            raise HeaderError(reply_dict['header'])


## Guide server REP interface
#############################


class GuideReplyInterface(ReplyInterface):
    """An interface for replies in the Guide REQ-REP pattern

    This interface should be associated with the EventManager service, inducing
    API calls corresponding to user input actions and/or responding with the
    requested information.
    """


    def process_request(self) -> None:
        """Process a received request

        When called, process the next request message in the queue from the
        Guide.
        The actual actions taken depend on the type of request, ie. the message
        header.

        Unrecognized but structurally-valid messages will not raise an error,
        but will instead result in a reply with an error header.
        """

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
            mp_list = [measurement_params.from_json(mm) for mm in body]
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

