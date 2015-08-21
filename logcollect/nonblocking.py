# coding: utf-8

# $Id: $

# Override lots of classes to prevent blocking on AMQP server connect.

from socket import SOL_TCP
import socket

from amqp import Connection
from amqp import transport
from amqp.utils import set_cloexec, get_errno


# noinspection PyUnresolvedReferences
class NonBlockingMixin(object):
    # noinspection PyMissingConstructor
    def __init__(self, host, connect_timeout):
        # Copy whole constructor from amqp.transport._AbstractTransport to
        # comment out one single line
        self.connected = True
        # noinspection PyUnusedLocal
        msg = None
        port = transport.AMQP_PORT

        m = transport.IPV6_LITERAL.match(host)
        if m:
            host = m.group(1)
            if m.group(2):
                port = int(m.group(2))
        else:
            if ':' in host:
                host, port = host.rsplit(':', 1)
                port = int(port)

        self.sock = None
        last_err = None
        for res in socket.getaddrinfo(host, port, 0,
                                      socket.SOCK_STREAM, SOL_TCP):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
                try:
                    set_cloexec(self.sock, True)
                except NotImplementedError:
                    pass
                self.sock.settimeout(connect_timeout)
                self.sock.connect(sa)
            except socket.error as exc:
                msg = exc
                self.sock.close()
                self.sock = None
                last_err = msg
                continue
            break

        if not self.sock:
            # Didn't connect, return the most recent error message
            raise socket.error(last_err)

        try:
            # Here is the magic: disable unlimited timeout while waiting
            # for amqp hello message

            # self.sock.settimeout(None)

            self.sock.setsockopt(SOL_TCP, socket.TCP_NODELAY, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            self._setup_transport()

            self._write(transport.AMQP_PROTOCOL_HEADER)
        except (OSError, IOError, socket.error) as exc:
            # noinspection PyProtectedMember
            if get_errno(exc) not in transport._UNAVAIL:
                self.connected = False
            raise


class NonBlockingTCPTransport(NonBlockingMixin, transport.TCPTransport):
    pass


class NonBlockingSSLTransport(NonBlockingMixin, transport.SSLTransport):
    def __init__(self, host, connect_timeout, ssl):
        if isinstance(ssl, dict):
            self.sslopts = ssl
        self._read_buffer = transport.EMPTY_BUFFER
        # Expect NonBlockingMixin.__init__ call
        super(NonBlockingSSLTransport, self).__init__(host, connect_timeout)


def create_transport(host, connect_timeout, ssl=False):
    """Given a few parameters from the Connection constructor,
    select and create a subclass of _AbstractTransport."""
    if ssl:
        return NonBlockingSSLTransport(host, connect_timeout, ssl)
    else:
        return NonBlockingTCPTransport(host, connect_timeout)


class NonBlockingConnection(Connection):
    def Transport(self, host, connect_timeout, ssl=False):
        return create_transport(host, connect_timeout, ssl)
