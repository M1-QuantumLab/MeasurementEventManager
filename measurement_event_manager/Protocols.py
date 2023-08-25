'''
Parsing and (un)packing messages for the various MEM protocols.
'''


###############################################################################
## Base Protocol class
###############################################################################

class Protocol(object):
    '''The base Protocol class

    Not intended to be used as a standalone, should be subclassed.
    '''
    protocol_id = None

    def __init__(self, logger):
        self.logger = logger


    def process_request(self, socket):
        ## Read request from socket
        request_msg = socket.recv_multipart()
        self.logger.debug('Request received: {}'.format(request_msg))

        ## Identify request protocol
        req_protocol = request_msg[0]
        if not (req_protocol == self.protocol_id):
            ## The protocol is not what is expected
            self.logger.error('Unexpected protocol {}'.format(req_protocol))
            ## TODO we need to actually send a response here
            ## otherwise the requesting socket will hang
            return False
        
        ## Process remaining content
        response = self.parse_request_content(request_msg[1:])

        ## Ensure the response is encoded
        response_enc = [xx.encode() for xx in response]
        ## Append protocol identifier to response content
        response_msg = [self.protocol_id.encode()] + response_enc
        ## Send response
        socket.send_multipart(response_msg)
        self.logger.debug('Response sent: {}'.format(response_msg))


    def parse_request_content(self, request):
        '''Null parser function to be overwritten in subclasses.
        '''
        return []


###############################################################################
## Guide protocol - MEM-GR
###############################################################################


class GuideProtocol(Protocol):
    '''Protocol definitions for MEM-GR messages.
    '''
    protocol_id = 'MEM-GR/0.1'

    def parse_request_content(self, request):

        ## Placeholder list so we can append response content to it
        response_content = []

        ## Separate out the request header
        header = request[0]
        content = request[1:]

        if header == 'IDN':
            self.logger.info('IDN request received.')
            response_header = 'IDN'
            ## TODO figure out the best way to get ID info to this point
            response_content.append('')

        elif header == 'ADD':
            self.logger.info('ADD request received.')
            ## TODO interface with the queuing system
            response_header = 'ADD'
            response_content.append('Not implemented!')

        else:
            self.logger.error('Unknown request header {}'.format(header))
            response_header = 'ERR'
            response_content.append('Unknown request header {}'.format(header))

        ## Return the header and content as a single list for multipart msg
        return [response_header] + response_content


###############################################################################
## Measurement protocol - MEM-MS
###############################################################################


class MeasurementProtocol(Protocol):
    '''Protocol definitions for MEM-MS messages.
    '''
    protocol_id = 'MEM-MS/0.1'

    def parse_request_content(self, request):

        ## Placeholder list so we can append content to it
        response_content = []

        ## Separate out the request header
        header = request[0]
        content = request[1:]

        if header == 'START':
            response_header = 'ACK'
            pass

        elif header == 'END':
            response_header = 'ACK'
            pass

        ## Return the header and content as a single list for multipart msg
        return [response_header] + response_content
