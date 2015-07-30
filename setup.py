from distutils.core import setup

setup(
    name='logcollect',
    version='0.8',
    packages=['logcollect'],
    url='http://github.com/rutube/logcollect/',
    license='Beer license',
    author='tumbler',
    author_email='zimbler@gmail.com',
    description='Helper for collecting logs to ELK stack via RabbitMQ',
    setup_requires=['amqp']
)
