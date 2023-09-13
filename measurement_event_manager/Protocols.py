'''
Parsing and (un)packing messages for the various MEM protocols.
'''

from measurement_event_manager import MeasurementParams
from measurement_event_manager.MeasurementQueue import QueueEmptyError


###############################################################################
## Incoming/parser protocol definitions
###############################################################################


def gr_parser(logger, request_content,
              queue,
              fetch_callback=lambda *args: None,
              *args):
    '''Parse MEM-GR/0.1 requests
    '''

    ## Placeholder list so we can append response content to it
    response_body = []

    ## Separate out the request header
    header = request_content[0]
    content = request_content[1:]

    if header == 'IDN':
        logger.info('IDN request received.')
        response_header = 'IDN'
        ## TODO Write proper IDN info
        response_body.append('')

    elif header == 'ADD':
        logger.info('ADD request received.')
        ## Iterate over each measurement parameter set provided
        for mp_spec in content:
            ## Construct MeasurementParams object from JSON content
            new_mp = MeasurementParams.from_json(mp_spec)
            ## Add to the MeasurementQueue
            added_index = queue.add(new_mp)
            ## Add the index to the response body
            response_body.append(str(added_index))
        ## Set response header
        response_header = 'ADD'

    elif header == 'QUE':
        logger.info('QUE request received.')
        response_header = 'QUE'
        queue_list = queue.info()
        for meas_item in queue_list:
            response_body.append(meas_item.to_json())

    elif header == 'LEN':
        logger.info('LEN request received.')
        response_header = 'LEN'
        response_body.append(str(len(queue)))

    elif header == 'RMV':
        logger.info('RMV request received.')
        index_list = []
        ## Convert received indices to int
        if content:
            for index in content:
                try:
                    index_int = int(index)
                except ValueError:
                    logger.error('{} could not be converted to an int'\
                                      .format(index))
                    continue
                else:
                    index_list.append(index_int)
        ## Remove values from queue
        try:
            removed_indices = queue.remove(index_list)
        except QueueEmptyError:
            logger.error("Attempting to remove items from empty queue")
            response_header = "ERR"
            response_body.append("Queue is empty; cannot remove items.")
        else:
            response_header = "RMV"
            response_body.extend(str(ii) for ii in removed_indices)

    elif header == 'FCH':
        logger.info('FCH request received.')
        if content:
            counter = content[0]
        else:
            counter = None
        ## Call the fetch callback function
        response_header = 'FCH'
        response_body.append(str(fetch_callback(counter)))

    ## TODO add more possible requests

    else:
        logger.error('Unknown request header {}'.format(header))
        response_header = 'ERR'
        response_body.append('Unknown request header {}'.format(header))

    ## Return the header and content as a single list for multipart msg
    response_content = [response_header] + response_body
    ## Make sure it's encoded into binary
    return [xx.encode() for xx in response_content if xx is not None]


def ms_parser(logger, request_content,
              req_callback=lambda *args: None,
              start_callback=lambda *args: None,
              end_callback=lambda *args: None,
              *args):
    '''Parse MEM-MS/0.1 requests
    '''

    ## Placeholder list so we can append content to it
    response_body = []

    ## Separate out the request header
    request_header = request_content[0]
    request_body = request_content[1:]

    if request_header == 'REQ':
        response_header = 'REQ'
        response_body.append(req_callback())

    if request_header == 'START':
        response_header = 'ACK'
        response_body.append(start_callback())

    elif request_header == 'END':
        response_header = 'ACK'
        response_body.append(end_callback(request_body))

    ## Return the header and content as a single list for multipart msg
    response_content = [response_header] + response_body
    ## Make sure it's encoded into binary
    return [xx.encode() for xx in response_content if xx is not None]


###############################################################################
## Outgoing/publisher protocol definitions
###############################################################################


def ls_publisher(logger, pub_content):
    '''Prepare MEM-LS/0.1 pub broadcasts
    '''

    ## Placeholder list so we can append to it
    pub_body = []

    ## Measurement successfully finished
    pub_header = "FIN"
    ## Pass the content directly to the message body
    ## This should be the measurement data
    pub_body.append(pub_content)

    ## Return the head and body as a single list for a multipart msg
    pub_content = [pub_header] + pub_body
    ## Make sure it's encoded into binary
    return [xx.encode() for xx in pub_content if xx is not None]


###############################################################################
## Protocol mappings
###############################################################################

## TODO these should eventually go into some config files

## Available protocols for each socket type
SOCKET_PROTOCOLS = {
    'guide': [
        'MEM-GR/0.1',
    ],
    'measurement': [
        'MEM-MS/0.1',
    ],
}

OUTGOING_PROTOCOLS = {
    'listener': [
        'MEM-LS/0.1',
    ],
}

## Parsers for each protocol
PROTOCOL_PARSERS = {
    'MEM-GR/0.1': gr_parser,
    'MEM-MS/0.1': ms_parser,
}

OUTGOING_PUBLISHERS = {
    'MEM-LS/0.1': ls_publisher,
}


###############################################################################
## High-level request processing functions
###############################################################################


def process_request(socket, socket_type, logger, **kwargs):
    '''Generic processor for incoming requests

    Selects the appropriate parser based on the socket_type and request
    protocol conformance. Any additional kwargs are passed to the parser, to
    allow the request to modify eg the state of a MeasurementQueue.
    '''
    ## Fetch the request from the socket
    request = socket.recv_multipart()
    logger.debug('Request received:')
    logger.debug(request)

    ## Extract the message protocol used
    req_protocol = request[0]
    ## If this is a valid protocol for the given socket type, pass it to the
    ## appropriate parser
    if req_protocol in SOCKET_PROTOCOLS[socket_type]:
        ## Fetch the right parser
        parser = PROTOCOL_PARSERS[req_protocol]
        ## Get the response and carry out instructed operations 
        ## Note that kwargs such as the MeasurementQueue object are passed to
        ## the parser, so their state can be modified by the incoming request
        ## via their exposed API calls.
        response_content = parser(logger, request[1:], **kwargs)

    else:
        ## Not a valid protocol for the socket type!
        logger.error('Invalid protocol {} for socket type {}'.format(
                                                    req_protocol, socket_type))
        ## This will return an error message marked with the same protocol
        response_content = [b'ERR']

    ## Prepare the response message
    response = [req_protocol.encode()] + response_content
    ## Send the response
    socket.send_multipart(response)


def publish_data(socket, socket_type, protocol, content, logger, **kwargs):
    '''Generic processor for outgoing pub-style broadcasting
    '''
    ## If this is a valid protocol for the given socket type, pass it to the
    ## appropriate publisher
    if protocol in OUTGOING_PROTOCOLS[socket_type]:
        ## Fetch the right publisher
        publisher = OUTGOING_PUBLISHERS[protocol]
        ## Get the content from the publisher
        pub_content = publisher(logger, content, **kwargs)
        ## Prepare the pub message
        pub_message = [protocol.encode()] + pub_content
        logger.debug('Sending request:')
        logger.debug(pub_message)
        ## Send the broadcast
        socket.send_multipart(pub_message)

    else:
        ## Not a valid protocol for the socket type!
        logger.error('Invalid protocol {} for socket type {}'.format(
                                                        protocol, socket_type))
        ## We can't really send any messages, so do nothing

