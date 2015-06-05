# coding: utf-8

# $Id: $
from logging.handlers import SocketHandler

from kombu import Connection


class AMQPHandler(SocketHandler, object):

    def __init__(self, broker_uri='amqp://localhost/', exchange='logstash',
                 exchange_type='fanout',
                 message_type='logstash', tags=None,
                 durable=False, version=0, extra_fields=True, fqdn=False,
                 facility=None, routing_key='logstash'):
        super(AMQPHandler, self).__init__(None, None)
        self.broker_uri = broker_uri
        self.exchange = exchange
        self.routing_key = routing_key

    def makeSocket(self, **kwargs):
        return AMQPSocket(self.broker_uri, self.exchange, self.routing_key)

    def makePickle(self, record):
        return self.formatter.format(record)


class AMQPSocket(object):

    def __init__(self, broker_uri, exchange, routing_key):
        self.conn = Connection(broker_uri)
        self.is_logging = False
        self.exchange = exchange
        self.routing_key = routing_key

    def sendall(self, data):
        if self.is_logging:
            return
        self.is_logging = True
        try:
            channel = self.conn.default_channel
            msg = channel.prepare_message(data)
            channel.basic_publish(msg, self.exchange, self.routing_key)
        finally:
            self.is_logging = False

    def close(self):
        self.conn.close()