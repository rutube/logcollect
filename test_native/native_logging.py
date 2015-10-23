# coding: utf-8

# $Id: $
from logging import getLogger
import random

from logcollect.boot import default_config

h = default_config('amqp://guest:guest@127.0.0.1/',
                   activity_identity={'project': 'logcollect',
                                      'subsystem': 'native_test'})

logger = getLogger("test")

logger.info("%s" % random.random())


