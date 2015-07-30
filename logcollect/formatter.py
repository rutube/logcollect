# coding: utf-8

# $Id: $
import json
import logging
import socket
import sys
from datetime import datetime
import traceback


class AMQPLogstashFormatter(logging.Formatter):

    skip_list = (
        'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
        'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
        'msecs', 'message', 'msg', 'name', 'pathname', 'processName',
        'relativeCreated', 'thread', 'threadName')

    def __init__(self, message_type='Logstash', tags=None, fqdn=False,
                 activity_identity={}, max_seq_no=1000):
        super(AMQPLogstashFormatter, self).__init__()
        self.message_type = message_type
        self.tags = tags if tags is not None else []
        self._seq_no = 1
        self._max_seq_no = max_seq_no
        self.ts = None

        if fqdn:
            self.host = socket.getfqdn()
        else:
            self.host = socket.gethostname()

        self.activity_identity = activity_identity
        self.skip_list = set(self.skip_list) - set(activity_identity.keys())

    def get_debug_fields(self, record):
        fields = {
            'exc_info': self.format_exception(record.exc_info),
            'lineno': record.lineno,
            'process': record.process,
            'threadName': record.threadName,
        }

        # funcName was added in 2.5
        if not getattr(record, 'funcName', None):
            fields['funcName'] = record.funcName

        # processName was added in 2.6
        if not getattr(record, 'processName', None):
            fields['processName'] = record.processName

        return fields

    @classmethod
    def format_source(cls, message_type, host, path):
        return "%s://%s/%s" % (message_type, host, path)

    @classmethod
    def format_timestamp(cls, time):
        tstamp = datetime.fromtimestamp(time)
        dt = tstamp.strftime("%Y-%m-%dT%H:%M:%S")
        msec = tstamp.microsecond / 1000
        return '%s.%03dZ' % (dt, msec)

    @classmethod
    def format_exception(cls, exc_info):
        if not exc_info:
            return ''
        exception = traceback.format_exception(*exc_info)
        return ''.join(exception)

    @classmethod
    def serialize(cls, message):
        if sys.version_info < (3, 0):
            return json.dumps(message)
        else:
            # noinspection PyArgumentList
            return bytes(json.dumps(message), 'utf-8')

    def get_seq_no(self, created):
        if created != self.ts:
            self.ts = created
            self._seq_no = 0
        if self._seq_no < self._max_seq_no:
            self._seq_no += 1
        return self._seq_no

    def format(self, record):
        # Create message dict
        message = {
            '@timestamp': self.format_timestamp(record.created),
            '@version': 1,
            'message': record.getMessage(),
            'host': self.host,
            'tags': self.tags,
            'type': self.message_type,
            'seq': self.get_seq_no(record.created),
            # Extra Fields
            'levelname': record.levelname,
            'logger': record.name,
        }

        # Add extra fields
        message.update(self.get_extra_fields(record))
        message.update(self.activity_identity)

        # If exception, add debug info
        if record.exc_info:
            message.update(self.get_debug_fields(record))

        return self.serialize(message)

    def get_extra_fields(self, record):
        # The list contains all the attributes listed in
        # http://docs.python.org/library/logging.html#logrecord-attributes

        if sys.version_info < (3, 0):
            easy_types = (basestring, bool, dict, float, int, long, list,
                          type(None))
        else:
            easy_types = (str, bool, dict, float, int, list, type(None))

        fields = {}

        for key, value in record.__dict__.items():
            if key not in self.skip_list:
                if isinstance(value, easy_types):
                    fields[key] = value
                else:
                    fields[key] = repr(value)

        return fields