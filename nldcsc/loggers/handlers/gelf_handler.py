import re
from logging.handlers import SocketHandler

from pygelf import GelfUdpHandler, GelfTcpHandler, GelfTlsHandler


class DCSCSocketHandler(SocketHandler):
    def __init__(self, host: str, port: int | None):
        super().__init__(host, port)

    def emit(self, record):
        """
        Emit a record.

        Pickles the record and writes it to the socket in binary format.
        If there is an error with the socket, silently drop the packet.
        If there was a problem with the socket, re-establishes the
        socket.
        """

        # parse out ansi color tags..
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        record.msg = ansi_escape.sub("", record.msg)

        try:
            s = self.makePickle(record)
            self.send(s)
        except Exception:
            self.handleError(record)


class DCSCGelfUDPHandler(GelfUdpHandler, DCSCSocketHandler):
    def __init__(self, host, port, **kwargs):
        super().__init__(host, port, **kwargs)


class DCSCGelfTCPHandler(GelfTcpHandler, DCSCSocketHandler):
    def __init__(self, host, port, **kwargs):
        super().__init__(host, port, **kwargs)


class DCSCGelfTLSHandler(GelfTlsHandler, DCSCSocketHandler):
    def __init__(self, host, port, **kwargs):
        super().__init__(host, port, **kwargs)
