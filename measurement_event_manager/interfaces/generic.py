import logging

import zmq

from measurement_event_manager.util.errors import (
    SocketUnavailableError,
    ConnectionTimeoutError,
)


###############################################################################
## Generic messaging interfaces
###############################################################################


## Base messaging interface
###########################


class MessageInterface(object):


    def __init__(self, socket=None, protocol_name=None, logger=None):
        if logger is None:
            self.logger = logging.getLogger(__name__)\
                                 .addHandler(logging.NullHandler())
        else:
            self.logger = logger
        self.set_socket(socket)
        self.protocol_name = protocol_name


    def set_socket(self, socket=None):
        if socket is not None:
            self.socket = socket
            self.logger.debug('Socket updated.')
            return True


    def _pack_message(self, header, body=None):
        full_message_raw = [self.protocol_name, header]
        if body:
            full_message_raw.extend(body)
        full_message = [xx.encode() for xx in full_message_raw]
        return full_message


    def _unpack_message(self, message_raw):
        ## Decode all parts of the message from binary
        message = [part.decode() for part in message_raw]
        ## Assign parts to output dict
        message_dict = {
            "protocol": message[0],
            "header": message[1],
            "body": message[2:],
        }
        return message_dict


    def _send_message(self, header, body=None):
        ## Make sure we have an open socket
        if (self.socket is None) or (self.socket.closed):
            raise SocketUnavailableError

        ## Pack message
        message = self._pack_message(header, body)

        ## Send the message
        self.logger.debug('Sending message:')
        self.logger.debug(message)
        self.socket.send_multipart(message)


## Request interface for REQ-REP
################################


class RequestInterface(MessageInterface):

    def _send_request(self, header, body=None):

        ## Package and send the request
        self._send_message(header, body)

        ## Wait for the response
        try:
            reply_wrapped = self.socket.recv_multipart()
        except zmq.error.Again:
            self.socket.close()
            raise ConnectionTimeoutError
        
        ## Unpack the response
        self.logger.debug('Received reply:')
        self.logger.debug(reply_wrapped)
        reply_dict = self._unpack_message(reply_wrapped)
        return reply_dict


## Reply interface for REQ-REP
##############################


class ReplyInterface(MessageInterface):


    def __init__(self, server, **kwargs):
        self._server = server
        super(ReplyInterface, self).__init__(**kwargs)


    def _receive_request(self):

        ## Receive and unpack request
        request_wrapped = self.socket.recv_multipart()
        self.logger.debug('Received request:')
        self.logger.debug(request_wrapped)
        request_dict = self._unpack_message(request_wrapped)

        return request_dict
    

    def _send_reply(self, header, body):

        ## Package and send the reply
        self._send_message(header, body)


## Broadcast interface for PUB-SUB
##################################


class BroadcastInterface(MessageInterface):

    def _send_broadcast(self, header, body):
        
        self._send_message(header, body)

