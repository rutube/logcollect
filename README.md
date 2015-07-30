# logcollect

Python library for centralized log collecting

Provides simple configuration for collecting python logs to ELK stack via
RabbitMQ.

Supported message flow is following:

```

python.logging
      ||
      \/
  logcollect
      ||
      \/
   RabbitMQ  
      ||
      \/
   Logstash
      ||
      \/
 ElasticSearch
      ||
      \/
    Kibana

```

## Mechanics

### Native logging

`logcollect.boot.default_config` ensures that root logger has correctly
configured amqp handler.

### Django
`logcollect.boot.django_dict_config` modifies `django.conf.settings.LOGGING`
to ensure correct amqp handler for root logger.
It should be called in settings module after LOGGING definition.

### Celery

`logcollect.boot.celery_config` adds signal handler for `worker_process_init`
signal, and after that adds amqp handler to `task_logger` base handler.
If necessary, root logger can be also attached to amqp handler.


## Tips for configuration

### Logstash

```ruby

input {
  rabbitmq {
    exchange => "logstash"
    queue => "logstash"
    host => "rabbitmq-host"
    type => "amqp"
    durable => true
    codec => "json"
  }
}
output {
  elasticsearch { host => localhost }
  stdout { codec => rubydebug }
}

```

### logcollect

All boot helpers have same parameters:

* broker_uri - celery-style RabbitMQ connection string, i.e.
`amqp://guest@localhost//vhost`
* exchange, routing_key - message routing info for RabbitMQ
* durable - message delivery mode
* level - handler loglevel
* activity_identity - dict with "process type info"

### Activity Identity

Assuming we deployed two projects on same host: "github" and "jenkins".
Both have web backends and background workers.
Activity identity helps to identify messages from these workers:

Project |   Worker   | Activity identity
------- | ---------- | -----------------
github  |  backend   | `{"project": "github", "application": "backend"}`
jenkins | background | `{"project": "jenkins", "application": "background"}`

`loggername` could be used for separating different parts of code within a
worker. Hostnames and process PIDs are added automatically.

### Correlation ID

Not supported yet, but idea is marking log messages about same object with ID
information about this object.


## Examples

### Native python logging

```sh
 python test_native/native_logging.py

```

### Django

```sh
 python test_django/manage.py test_log

```

### Celery

First, start worker:

```sh
celery worker -A test_celery.app.celery
```

Then send a task to that worker:

```sh
python test_celery/send_task.py
```

## Related works

AMQPHandler and AMQPLogstashFormatter are copied from
[python-logstash](https://github.com/vklochan/python-logstash).

See also:
* [RabbitMQ](https://github.com/rabbitmq/rabbitmq-server)
* [Logstash](https://github.com/elastic/logstash)
* [Kibana](https://github.com/elastic/kibana)
* [Django](https://github.com/django/django)
* [Celery](https://github.com/celery/celery)
