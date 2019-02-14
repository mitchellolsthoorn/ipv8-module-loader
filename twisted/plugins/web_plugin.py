import logging
import signal
import sys

from twisted.application.service import IServiceMaker, MultiService
from twisted.internet import reactor
from twisted.plugin import IPlugin
from twisted.python import usage
from twisted.python.log import msg
from twisted.web import server
from twisted.web.static import File
from zope.interface import implements


class Options(usage.Options):
    optParameters = [
        ['port', 'p', 80, "Use an alternative port for web server", int],
    ]


class WebServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "dapp-web"
    description = "dApp web application"
    options = Options

    def __init__(self):
        """
        Initialize the variables of this service and the logger.
        """

        # Init service state
        self._stopping = False

        # Init variables
        self.service = None

        # Setup logging
        root = logging.getLogger()
        root.setLevel(logging.INFO)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.INFO)
        stderr_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s"))
        root.addHandler(stderr_handler)

    def start(self, options, service):
        """
        Main method to startup the cli and add a signal handler.
        """

        msg("Service: Starting")

        reactor.listenTCP(10000, server.Site(File("web")))

        def signal_handler(sig, _):
            msg("Service: Received shut down signal %s" % sig)
            if not self._stopping:
                self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def stop(self):
        self._stopping = True
        reactor.stop()

    def makeService(self, options):
        """
        Construct a IPv8 service.
        """

        web_service = MultiService()
        web_service.setName("dapp-web")

        reactor.callWhenRunning(self.start, options, web_service)

        return web_service


service_maker = WebServiceMaker()
