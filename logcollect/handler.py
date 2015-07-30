# coding: utf-8

# $Id: $
from logging.handlers import SocketHandler
from urlparse import urlparse

from amqp import Message
from amqp.connection import Connection, AMQP_LOGGER


class AMQPHandler(SocketHandler, object):

    def __init__(self, broker_uri='amqp://localhost/', exchange='logstash',
                 exchange_type='fanout',
                 message_type='logstash', tags=None,
                 durable=True, version=0, extra_fields=True, fqdn=False,
                 facility=None, routing_key='logstash'):
        super(AMQPHandler, self).__init__(None, None)
        self.broker_uri = broker_uri
        self.exchange = exchange
        self.routing_key = routing_key
        self.exchange_type = exchange_type
        self.durable = durable

    def emit(self, record):
        return super(AMQPHandler, self).emit(record)

    def makeSocket(self, **kwargs):
        propagate = AMQP_LOGGER.propagate
        try:
            AMQP_LOGGER.propagate = False
            amqp_socket = AMQPSocket(self.broker_uri,
                                     self.exchange,
                                     self.exchange_type,
                                     self.routing_key,
                                     self.durable)
        finally:
            AMQP_LOGGER.propagate = propagate
        return amqp_socket

    def makePickle(self, record):
        return self.formatter.format(record)


class AMQPSocket(object):

    def __init__(self, broker_uri, exchange, exchange_type, routing_key,
                 durable):
        self.is_logging = True
        self.conn = Connection(**self._parse_broker_uri(broker_uri))
        self.channel = self.conn.channel()
        self.channel.exchange_declare(exchange=exchange,
                                      type=exchange_type,
                                      durable=durable,
                                      auto_delete=not durable)
        self.is_logging = False
        self.exchange = exchange
        self.routing_key = routing_key

    def sendall(self, data):
        if self.is_logging:
            return
        self.is_logging = True
        try:
            msg = Message(data)
            self.channel.basic_publish(msg, self.exchange, self.routing_key)
        finally:
            self.is_logging = False

    def close(self):
        self.conn.close()

    @staticmethod
    def _parse_broker_uri(broker_uri):
        url = urlparse(broker_uri)
        return {
            'host': url.hostname,
            'virtual_host': url.path,
            'userid': url.username,
            'password': url.password
        }