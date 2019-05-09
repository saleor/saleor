"""Transport implementation."""
# Copyright (C) 2009 Barry Pederson <bp@barryp.org>
from __future__ import absolute_import, unicode_literals

import errno
import re
import socket
import ssl
from contextlib import contextmanager

from .exceptions import UnexpectedFrame
from .five import items
from .platform import KNOWN_TCP_OPTS, SOL_TCP, pack, unpack
from .utils import get_errno, set_cloexec

try:
    from ssl import SSLError
except ImportError:  # pragma: no cover
    class SSLError(Exception):  # noqa
        """Dummy SSL exception."""

_UNAVAIL = {errno.EAGAIN, errno.EINTR, errno.ENOENT, errno.EWOULDBLOCK}

AMQP_PORT = 5672

EMPTY_BUFFER = bytes()

SIGNED_INT_MAX = 0x7FFFFFFF

# Yes, Advanced Message Queuing Protocol Protocol is redundant
AMQP_PROTOCOL_HEADER = 'AMQP\x00\x00\x09\x01'.encode('latin_1')

# Match things like: [fe80::1]:5432, from RFC 2732
IPV6_LITERAL = re.compile(r'\[([\.0-9a-f:]+)\](?::(\d+))?')

DEFAULT_SOCKET_SETTINGS = {
    'TCP_NODELAY': 1,
    'TCP_USER_TIMEOUT': 1000,
    'TCP_KEEPIDLE': 60,
    'TCP_KEEPINTVL': 10,
    'TCP_KEEPCNT': 9,
}


def to_host_port(host, default=AMQP_PORT):
    """Convert hostname:port string to host, port tuple."""
    port = default
    m = IPV6_LITERAL.match(host)
    if m:
        host = m.group(1)
        if m.group(2):
            port = int(m.group(2))
    else:
        if ':' in host:
            host, port = host.rsplit(':', 1)
            port = int(port)
    return host, port


class _AbstractTransport(object):
    """Common superclass for TCP and SSL transports."""

    def __init__(self, host, connect_timeout=None,
                 read_timeout=None, write_timeout=None,
                 socket_settings=None, raise_on_initial_eintr=True, **kwargs):
        self.connected = False
        self.sock = None
        self.raise_on_initial_eintr = raise_on_initial_eintr
        self._read_buffer = EMPTY_BUFFER
        self.host, self.port = to_host_port(host)
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        self.socket_settings = socket_settings

    def connect(self):
        try:
            # are we already connected?
            if self.connected:
                return
            self._connect(self.host, self.port, self.connect_timeout)
            self._init_socket(
                self.socket_settings, self.read_timeout, self.write_timeout,
            )
            # we've sent the banner; signal connect
            # EINTR, EAGAIN, EWOULDBLOCK would signal that the banner
            # has _not_ been sent
            self.connected = True
        except (OSError, IOError, SSLError):
            # if not fully connected, close socket, and reraise error
            if self.sock and not self.connected:
                self.sock.close()
                self.sock = None
            raise

    @contextmanager
    def having_timeout(self, timeout):
        if timeout is None:
            yield self.sock
        else:
            sock = self.sock
            prev = sock.gettimeout()
            if prev != timeout:
                sock.settimeout(timeout)
            try:
                yield self.sock
            except SSLError as exc:
                if 'timed out' in str(exc):
                    # http://bugs.python.org/issue10272
                    raise socket.timeout()
                elif 'The operation did not complete' in str(exc):
                    # Non-blocking SSL sockets can throw SSLError
                    raise socket.timeout()
                raise
            except socket.error as exc:
                if get_errno(exc) == errno.EWOULDBLOCK:
                    raise socket.timeout()
                raise
            finally:
                if timeout != prev:
                    sock.settimeout(prev)

    def _connect(self, host, port, timeout):
        e = None

        # Below we are trying to avoid additional DNS requests for AAAA if A
        # succeeds. This helps a lot in case when a hostname has an IPv4 entry
        # in /etc/hosts but not IPv6. Without the (arguably somewhat twisted)
        # logic below, getaddrinfo would attempt to resolve the hostname for
        # both IP versions, which would make the resolver talk to configured
        # DNS servers. If those servers are for some reason not available
        # during resolution attempt (either because of system misconfiguration,
        # or network connectivity problem), resolution process locks the
        # _connect call for extended time.
        addr_types = (socket.AF_INET, socket.AF_INET6)
        addr_types_num = len(addr_types)
        for n, family in enumerate(addr_types):
            # first, resolve the address for a single address family
            try:
                entries = socket.getaddrinfo(
                    host, port, family, socket.SOCK_STREAM, SOL_TCP)
                entries_num = len(entries)
            except socket.gaierror:
                # we may have depleted all our options
                if n + 1 >= addr_types_num:
                    # if getaddrinfo succeeded before for another address
                    # family, reraise the previous socket.error since it's more
                    # relevant to users
                    raise (e
                           if e is not None
                           else socket.error(
                               "failed to resolve broker hostname"))
                continue  # pragma: no cover

            # now that we have address(es) for the hostname, connect to broker
            for i, res in enumerate(entries):
                af, socktype, proto, _, sa = res
                try:
                    self.sock = socket.socket(af, socktype, proto)
                    try:
                        set_cloexec(self.sock, True)
                    except NotImplementedError:
                        pass
                    self.sock.settimeout(timeout)
                    self.sock.connect(sa)
                except socket.error as ex:
                    e = ex
                    if self.sock is not None:
                        self.sock.close()
                        self.sock = None
                    # we may have depleted all our options
                    if i + 1 >= entries_num and n + 1 >= addr_types_num:
                        raise
                else:
                    # hurray, we established connection
                    return

    def _init_socket(self, socket_settings, read_timeout, write_timeout):
        self.sock.settimeout(None)  # set socket back to blocking mode
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self._set_socket_options(socket_settings)

        # set socket timeouts
        for timeout, interval in ((socket.SO_SNDTIMEO, write_timeout),
                                  (socket.SO_RCVTIMEO, read_timeout)):
            if interval is not None:
                sec = int(interval)
                usec = int((interval - sec) * 1000000)
                self.sock.setsockopt(
                    socket.SOL_SOCKET, timeout,
                    pack('ll', sec, usec),
                )
        self._setup_transport()

        self._write(AMQP_PROTOCOL_HEADER)

    def _get_tcp_socket_defaults(self, sock):
        tcp_opts = {}
        for opt in KNOWN_TCP_OPTS:
            enum = None
            if opt == 'TCP_USER_TIMEOUT':
                try:
                    from socket import TCP_USER_TIMEOUT as enum
                except ImportError:
                    # should be in Python 3.6+ on Linux.
                    enum = 18
            elif hasattr(socket, opt):
                enum = getattr(socket, opt)

            if enum:
                if opt in DEFAULT_SOCKET_SETTINGS:
                    tcp_opts[enum] = DEFAULT_SOCKET_SETTINGS[opt]
                elif hasattr(socket, opt):
                    tcp_opts[enum] = sock.getsockopt(
                        SOL_TCP, getattr(socket, opt))
        return tcp_opts

    def _set_socket_options(self, socket_settings):
        tcp_opts = self._get_tcp_socket_defaults(self.sock)
        if socket_settings:
            tcp_opts.update(socket_settings)
        for opt, val in items(tcp_opts):
            self.sock.setsockopt(SOL_TCP, opt, val)

    def _read(self, n, initial=False):
        """Read exactly n bytes from the peer."""
        raise NotImplementedError('Must be overriden in subclass')

    def _setup_transport(self):
        """Do any additional initialization of the class."""
        pass

    def _shutdown_transport(self):
        """Do any preliminary work in shutting down the connection."""
        pass

    def _write(self, s):
        """Completely write a string to the peer."""
        raise NotImplementedError('Must be overriden in subclass')

    def close(self):
        if self.sock is not None:
            self._shutdown_transport()
            # Call shutdown first to make sure that pending messages
            # reach the AMQP broker if the program exits after
            # calling this method.
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.sock = None
        self.connected = False

    def read_frame(self, unpack=unpack):
        read = self._read
        read_frame_buffer = EMPTY_BUFFER
        try:
            frame_header = read(7, True)
            read_frame_buffer += frame_header
            frame_type, channel, size = unpack('>BHI', frame_header)
            # >I is an unsigned int, but the argument to sock.recv is signed,
            # so we know the size can be at most 2 * SIGNED_INT_MAX
            if size > SIGNED_INT_MAX:
                part1 = read(SIGNED_INT_MAX)
                part2 = read(size - SIGNED_INT_MAX)
                payload = b''.join([part1, part2])
            else:
                payload = read(size)
            read_frame_buffer += payload
            ch = ord(read(1))
        except socket.timeout:
            self._read_buffer = read_frame_buffer + self._read_buffer
            raise
        except (OSError, IOError, SSLError, socket.error) as exc:
            # Don't disconnect for ssl read time outs
            # http://bugs.python.org/issue10272
            if isinstance(exc, SSLError) and 'timed out' in str(exc):
                raise socket.timeout()
            if get_errno(exc) not in _UNAVAIL:
                self.connected = False
            raise
        if ch == 206:  # '\xce'
            return frame_type, channel, payload
        else:
            raise UnexpectedFrame(
                'Received {0:#04x} while expecting 0xce'.format(ch))

    def write(self, s):
        try:
            self._write(s)
        except socket.timeout:
            raise
        except (OSError, IOError, socket.error) as exc:
            if get_errno(exc) not in _UNAVAIL:
                self.connected = False
            raise


class SSLTransport(_AbstractTransport):
    """Transport that works over SSL."""

    def __init__(self, host, connect_timeout=None, ssl=None, **kwargs):
        self.sslopts = ssl if isinstance(ssl, dict) else {}
        self._read_buffer = EMPTY_BUFFER
        super(SSLTransport, self).__init__(
            host, connect_timeout=connect_timeout, **kwargs)

    def _setup_transport(self):
        """Wrap the socket in an SSL object."""
        self.sock = self._wrap_socket(self.sock, **self.sslopts)
        self.sock.do_handshake()
        self._quick_recv = self.sock.read

    def _wrap_socket(self, sock, context=None, **sslopts):
        if context:
            return self._wrap_context(sock, sslopts, **context)
        return self._wrap_socket_sni(sock, **sslopts)

    def _wrap_context(self, sock, sslopts, check_hostname=None, **ctx_options):
        ctx = ssl.create_default_context(**ctx_options)
        ctx.check_hostname = check_hostname
        return ctx.wrap_socket(sock, **sslopts)

    def _wrap_socket_sni(self, sock, keyfile=None, certfile=None,
                         server_side=False, cert_reqs=ssl.CERT_NONE,
                         ca_certs=None, do_handshake_on_connect=True,
                         suppress_ragged_eofs=True, server_hostname=None,
                         ciphers=None, ssl_version=None):
        """Socket wrap with SNI headers.

        Default `ssl.wrap_socket` method augmented with support for
        setting the server_hostname field required for SNI hostname header
        """
        opts = dict(sock=sock, keyfile=keyfile, certfile=certfile,
                    server_side=server_side, cert_reqs=cert_reqs,
                    ca_certs=ca_certs,
                    do_handshake_on_connect=do_handshake_on_connect,
                    suppress_ragged_eofs=suppress_ragged_eofs,
                    ciphers=ciphers)
        # Setup the right SSL version; default to optimal versions across
        # ssl implementations
        if ssl_version is not None:
            opts['ssl_version'] = ssl_version
        else:
            # older versions of python 2.7 and python 2.6 do not have the
            # ssl.PROTOCOL_TLS defined the equivalent is ssl.PROTOCOL_SSLv23
            # we default to PROTOCOL_TLS and fallback to PROTOCOL_SSLv23
            if hasattr(ssl, 'PROTOCOL_TLS'):
                opts['ssl_version'] = ssl.PROTOCOL_TLS
            else:
                opts['ssl_version'] = ssl.PROTOCOL_SSLv23
        sock = ssl.wrap_socket(**opts)
        # Set SNI headers if supported
        if (server_hostname is not None) and (
                hasattr(ssl, 'HAS_SNI') and ssl.HAS_SNI) and (
                hasattr(ssl, 'SSLContext')):
            context = ssl.SSLContext(opts['ssl_version'])
            context.verify_mode = cert_reqs
            context.check_hostname = True
            context.load_cert_chain(certfile, keyfile)
            sock = context.wrap_socket(sock, server_hostname=server_hostname)
        return sock

    def _shutdown_transport(self):
        """Unwrap a Python 2.6 SSL socket, so we can call shutdown()."""
        if self.sock is not None:
            try:
                unwrap = self.sock.unwrap
            except AttributeError:
                return
            self.sock = unwrap()

    def _read(self, n, initial=False,
              _errnos=(errno.ENOENT, errno.EAGAIN, errno.EINTR)):
        # According to SSL_read(3), it can at most return 16kb of data.
        # Thus, we use an internal read buffer like TCPTransport._read
        # to get the exact number of bytes wanted.
        recv = self._quick_recv
        rbuf = self._read_buffer
        try:
            while len(rbuf) < n:
                try:
                    s = recv(n - len(rbuf))  # see note above
                except socket.error as exc:
                    # ssl.sock.read may cause a SSLerror without errno
                    # http://bugs.python.org/issue10272
                    if isinstance(exc, SSLError) and 'timed out' in str(exc):
                        raise socket.timeout()
                    # ssl.sock.read may cause ENOENT if the
                    # operation couldn't be performed (Issue celery#1414).
                    if exc.errno in _errnos:
                        if initial and self.raise_on_initial_eintr:
                            raise socket.timeout()
                        continue
                    raise
                if not s:
                    raise IOError('Server unexpectedly closed connection')
                rbuf += s
        except:  # noqa
            self._read_buffer = rbuf
            raise
        result, self._read_buffer = rbuf[:n], rbuf[n:]
        return result

    def _write(self, s):
        """Write a string out to the SSL socket fully."""
        write = self.sock.write
        while s:
            try:
                n = write(s)
            except (ValueError, AttributeError):
                # AG: sock._sslobj might become null in the meantime if the
                # remote connection has hung up.
                # In python 3.2, an AttributeError is raised because the SSL
                # module tries to access self._sslobj.write (w/ self._sslobj ==
                # None)
                # In python 3.4, a ValueError is raised is self._sslobj is
                # None. So much for portability... :/
                n = 0
            if not n:
                raise IOError('Socket closed')
            s = s[n:]


class TCPTransport(_AbstractTransport):
    """Transport that deals directly with TCP socket."""

    def _setup_transport(self):
        # Setup to _write() directly to the socket, and
        # do our own buffered reads.
        self._write = self.sock.sendall
        self._read_buffer = EMPTY_BUFFER
        self._quick_recv = self.sock.recv

    def _read(self, n, initial=False, _errnos=(errno.EAGAIN, errno.EINTR)):
        """Read exactly n bytes from the socket."""
        recv = self._quick_recv
        rbuf = self._read_buffer
        try:
            while len(rbuf) < n:
                try:
                    s = recv(n - len(rbuf))
                except socket.error as exc:
                    if exc.errno in _errnos:
                        if initial and self.raise_on_initial_eintr:
                            raise socket.timeout()
                        continue
                    raise
                if not s:
                    raise IOError('Server unexpectedly closed connection')
                rbuf += s
        except:  # noqa
            self._read_buffer = rbuf
            raise

        result, self._read_buffer = rbuf[:n], rbuf[n:]
        return result


def Transport(host, connect_timeout=None, ssl=False, **kwargs):
    """Create transport.

    Given a few parameters from the Connection constructor,
    select and create a subclass of _AbstractTransport.
    """
    transport = SSLTransport if ssl else TCPTransport
    return transport(host, connect_timeout=connect_timeout, ssl=ssl, **kwargs)
