# Default library imports
import os

from binascii import hexlify

# Third party imports - Twisted
from twisted.protocols.basic import LineReceiver
from twisted.python.log import msg

from loader.community.dapp.core.dapp import DApp


class CLI(LineReceiver):
    delimiter = os.linesep

    header = "\
        .___  _____                         \n\
      __| _/ /  _  \  ______  ______  ______\n\
     / __ | /  /_\  \ \____ \ \____ \/  ___/\n\
    / /_/  /    |    \   |_> >   |_> >___ \ \n\
    \____  \____|__  /    __/ |   __/____  >\n\
         \/        \/ |__|    |__|       \/ \n"

    colors = {
        'blue': '\033[94m',
        'pink': '\033[95m',
        'green': '\033[92m',
    }

    MENU_MAIN = 0
    MENU_DAPP_LIST = 1
    MENU_DAPP = 2

    def __init__(self, service, ipv8, dapp_community):
        self.service = service
        self.ipv8 = ipv8
        self.dapp_community = dapp_community

        self.menu_level = self.MENU_MAIN
        self.current_option = None
        self.context = None  # type: DApp

        self.main_menu_items = [
            {"Create test dApp": self.create_test_dapp},
            {"Create dApp": self.create_dapp_setup},
            {"Show dApps": self.show_dapps},
            {"Exit": self.exit},
        ]

        self.dapp_menu_items = [
            {"Download dApp": self.download_dapp},
            {"Run dApp": self.run_dapp},
            {"Vote dApp": self.vote_dapp},
        ]

        self.print_main_menu()

    def _colorize(self, string, color):
        if color not in self.colors:
            return string

        return self.colors[color] + string + '\033[0m'

    def rawDataReceived(self, data):
        raise NotImplementedError

    def lineReceived(self, line):
        if self.current_option is None:
            if self.menu_level == self.MENU_MAIN:
                try:
                    if len(self.main_menu_items) - 1 < int(line) < 0:
                        raise ValueError

                    # Call the matching function
                    self.main_menu_items[int(line)].values()[0](line)
                except (ValueError, IndexError):
                    self.print_main_menu()
            elif self.menu_level == self.MENU_DAPP_LIST:
                try:
                    dapps = self.dapp_community.get_dapps_from_catalog()
                    if len(dapps) - 1 < int(line) < -1:
                        raise ValueError

                    if int(line) == -1:
                        self.menu_level = self.MENU_MAIN
                        self.current_option = None
                        self.context = None
                        self.print_main_menu()
                        return

                    self.show_dapp(int(line))
                except (ValueError, IndexError):
                    self.print_dapp_list_menu()
            elif self.menu_level == self.MENU_DAPP:
                try:
                    if len(self.dapp_menu_items) - 1 < int(line) < -1:
                        raise ValueError

                    if int(line) == -1:
                        self.menu_level = self.MENU_DAPP_LIST
                        self.current_option = None
                        self.context = None
                        self.print_dapp_list_menu()
                        return

                    # Call the matching function
                    self.dapp_menu_items[int(line)].values()[0](line)
                except (ValueError, IndexError):
                    self.print_dapp_menu()
            else:
                self.reset()
        else:
            self.current_option(line)

    def print_main_menu(self):
        os.system('clear')
        msg(self._colorize('\n' + self.header, 'pink'))
        msg(self._colorize('version 0.1', 'green'))
        for item in self.main_menu_items:
            msg(self._colorize("[" + str(self.main_menu_items.index(item)) + "] ", 'blue') + item.keys()[0])

    def print_dapp_list_menu(self):
        os.system('clear')
        msg(self._colorize('\n' + self.header, 'pink'))
        msg(self._colorize('version 0.1', 'green'))

        dapps = self.dapp_community.get_dapps_from_catalog()

        msg(self._colorize(str(len(dapps)) + " dApps found:", 'blue'))

        msg(self._colorize("[-1] ", 'blue') + self._colorize("Return to previous menu", 'green'))

        for dapp in dapps:
            msg(self._colorize("[" + str(dapps.index(dapp)) + "] ", 'blue') + self._colorize(str(dapp), 'green'))

    def print_dapp_menu(self):
        os.system('clear')
        msg(self._colorize('\n' + self.header, 'pink'))
        msg(self._colorize('version 0.1', 'green'))

        dapp = self.dapp_community.get_dapp_from_catalog(self.context.id)  # type: DApp

        msg(self._colorize("Creator: " + str(hexlify(dapp.id.creator)), 'green'))
        msg(self._colorize("Content Hash: " + str(dapp.id.content_hash), 'green'))
        msg(self._colorize("Name: " + str(dapp.name), 'green'))
        msg(self._colorize("Votes: " + str(dapp.votes), 'green'))

        msg(self._colorize("[-1] ", 'blue') + self._colorize("Return to previous menu", 'green'))

        for item in self.dapp_menu_items:
            msg(self._colorize("[" + str(self.dapp_menu_items.index(item)) + "] ", 'blue') + item.keys()[0])

    def reset(self):
        self.menu_level = self.MENU_MAIN
        self.current_option = self.OPTION_NONE
        self.context = None
        self.print_main_menu()

    def create_test_dapp(self, line):
        self.dapp_community.create_dapp_test()

        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def create_dapp_setup(self, line):
        self.current_option = self.create_dapp
        msg(self._colorize("Press enter dApp package name", 'green'))

    def create_dapp(self, line):
        msg(self._colorize("dApp name: " + line, 'blue'))
        self.dapp_community.create_dapp(line)

        self.current_option = None
        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def show_dapps(self, line):
        self.menu_level = self.MENU_DAPP_LIST
        self.print_dapp_list_menu()

    def show_dapp(self, line):
        dapps = self.dapp_community.get_dapps_from_catalog()
        index = int(line)

        msg("Number of dapps retrieved: " + str(len(dapps)))

        self.menu_level = self.MENU_DAPP
        self.context = dapps[index]  # type: DApp
        self.print_dapp_menu()

    def download_dapp(self, line):
        self.dapp_community.download_dapp(self.context.id)

        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def run_dapp(self, line):
        self.dapp_community.run_dapp(self.context.id)

        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def vote_dapp(self, line):
        self.dapp_community.vote_dapp(self.context.id)

        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def exit(self, line):
        self.service.stop()
