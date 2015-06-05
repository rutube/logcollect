# coding: utf-8

# $Id: $
from logging import getLogger

from logcollect.boot import default_config

h = default_config('amqp://192.168.70.85', activity_identity={'project': 'logcollect',
                                                              'subsystem': 'native_test'})

logger = getLogger("test")

logger.info("ROOT")


