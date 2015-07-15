# coding: utf-8

# $Id: $
from logging import getLogger
import random

from logcollect.boot import default_config

h = default_config('amqp://guest@localhost',
                   activity_identity={'project': 'logcollect',
                                      'subsystem': 'native_test'})

logger = getLogger("test")

logger.info("%s" % random.random())


