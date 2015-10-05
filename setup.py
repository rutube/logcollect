from distutils.core import setup

try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, 'r').read()

setup(
    name='logcollect',
    version='0.12.0',
    long_description=read_md('README.md'),
    packages=['logcollect'],
    url='http://github.com/rutube/logcollect/',
    license='Beerware',
    author='tumbler',
    author_email='zimbler@gmail.com',
    description='Helper for collecting logs to ELK stack via RabbitMQ',
    setup_requires=['amqp'],
)
