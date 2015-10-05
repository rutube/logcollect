# coding: utf-8

# $Id: $


from logging import root, _handlers, config

from celery import signals

from logcollect.formatter import AMQPLogstashFormatter
from logcollect.handler import AMQPHandler

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': []
        }
    }
}


def ensure_amqp_handler(broker_uri, exchange, routing_key, durable, auto_delete,
                        level, activity_identity, logger=None):
    amqp_handler = None
    logger = logger or root
    for h in _handlers.values():
        if isinstance(h, AMQPHandler):
            amqp_handler = h
    if amqp_handler is None:
        amqp_handler = AMQPHandler(broker_uri=broker_uri,
                                   exchange=exchange, durable=durable,
                                   auto_delete=auto_delete,
                                   routing_key=routing_key)
        amqp_handler.setFormatter(AMQPLogstashFormatter(
            activity_identity=activity_identity))
        amqp_handler.setLevel(level)
    root_handler = None
    for h in logger.handlers:
        if isinstance(h, AMQPHandler):
            root_handler = h
    if not root_handler:
        logger.addHandler(amqp_handler)
    return amqp_handler


def default_config(broker_uri='amqp://localhost/', exchange='logstash',
                   routing_key='logstash', durable=False, auto_delete=False,
                   level='DEBUG', activity_identity=None):
    config.dictConfig(LOGGING)
    activity_identity = activity_identity or {}
    return ensure_amqp_handler(broker_uri, exchange, routing_key, durable,
                               auto_delete, level, activity_identity)


def django_dict_config(LOGGING, broker_uri='amqp://localhost/',
                       exchange='logstash', routing_key='logstash',
                       durable=False, auto_delete=False, level='DEBUG',
                       activity_identity=None):
    LOGGING.setdefault('handlers', {})
    activity_identity = activity_identity or {}
    amqp_handler = None
    for name, handler_conf in LOGGING['handlers'].items():
        if handler_conf['class'] == 'logcollect.handler.AMQPHandler':
            amqp_handler = name

    if not amqp_handler:
        amqp_handler = 'logcollect'
        if amqp_handler in LOGGING['handlers']:
            raise ValueError("logcollect handler name conflict")
        handler_conf = {
            'class': 'logcollect.handler.AMQPHandler',
        }
        LOGGING['handlers'][amqp_handler] = handler_conf

    LOGGING.setdefault('formatters', {})
    amqp_formatter = None
    for name, formatter_conf in LOGGING['formatters'].items():
        if formatter_conf.get(
                '()') == 'logcollect.formatter.AMQPLogstashFormatter':
            amqp_formatter = name

    if not amqp_formatter:
        amqp_formatter = 'logcollect'
        if amqp_formatter in LOGGING['formatters']:
            raise ValueError("logcollect formatter name conflict")
        formatter_conf = {
            '()': 'logcollect.formatter.AMQPLogstashFormatter',
        }
        formatter_conf.setdefault('activity_identity', activity_identity)
        LOGGING['formatters'][amqp_formatter] = formatter_conf

    LOGGING.setdefault('loggers', {})
    LOGGING['loggers'].setdefault('', {})
    root_logger = LOGGING['loggers']['']
    root_logger.setdefault('handlers', [])
    if amqp_handler not in root_logger['handlers']:
        root_logger['handlers'].append(amqp_handler)
    root_logger.setdefault('level', level)

    handler_conf = LOGGING['handlers'][amqp_handler]
    handler_conf.setdefault('broker_uri', broker_uri)
    handler_conf.setdefault('exchange', exchange)
    handler_conf.setdefault('routing_key', routing_key)
    handler_conf.setdefault('durable', durable)
    handler_conf.setdefault('auto_delete', auto_delete)
    handler_conf.setdefault('level', level)
    handler_conf.setdefault('formatter', amqp_formatter)

    return amqp_handler


def celery_config(broker_uri='amqp://localhost/',
                  exchange='logstash', routing_key='logstash',
                  durable=True, level='DEBUG', auto_delete=False,
                  activity_identity=None, collect_root_logs=False):

    activity_identity = activity_identity or {}

    def init_logging(**kwargs):
        from celery.utils.log import task_logger
        if collect_root_logs:
            ensure_amqp_handler(broker_uri, exchange, routing_key, durable,
                                auto_delete, level, activity_identity,
                                logger=None)
        ensure_amqp_handler(broker_uri, exchange, routing_key, durable,
                            auto_delete, level, activity_identity,
                            logger=task_logger)

    signals.worker_process_init.connect(init_logging, weak=False)
    signals.worker_ready.connect(init_logging, weak=False)
