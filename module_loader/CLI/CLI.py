# Default library imports
import os

from binascii import hexlify

# Third party imports - Twisted
from twisted.protocols.basic import LineReceiver
from twisted.python.log import msg

from module_loader.community.module.core.module import Module


class CLI(LineReceiver):
    delimiter = os.linesep

    header = "\
     __  __           _       _        _                     _            \n\
    |  \/  |         | |     | |      | |                   | |           \n\
    | \  / | ___   __| |_   _| | ___  | |     ___   __ _  __| | ___ _ __  \n\
    | |\/| |/ _ \ / _` | | | | |/ _ \ | |    / _ \ / _` |/ _` |/ _ \ '__| \n\
    | |  | | (_) | (_| | |_| | |  __/ | |___| (_) | (_| | (_| |  __/ |    \n\
    |_|  |_|\___/ \__,_|\__,_|_|\___| |______\___/ \__,_|\__,_|\___|_|    \n"

    colors = {
        'blue': '\033[94m',
        'pink': '\033[95m',
        'green': '\033[92m',
    }

    MENU_MAIN = 0
    MENU_MODULE_LIST = 1
    MENU_MODULE = 2

    def __init__(self, service, ipv8, module_community):
        self.service = service
        self.ipv8 = ipv8
        self.module_community = module_community

        self.menu_level = self.MENU_MAIN
        self.current_option = None
        self.context = None  # type: Module

        self.main_menu_items = [
            {"Create test module": self.create_test_module},
            {"Create module": self.create_module_setup},
            {"Show modules": self.show_modules},
            {"Exit": self.exit},
        ]

        self.module_menu_items = [
            {"Download module": self.download_module},
            {"Run module": self.run_module},
            {"Vote module": self.vote_module},
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
            elif self.menu_level == self.MENU_MODULE_LIST:
                try:
                    modules = self.module_community.get_modules_from_catalog()
                    if len(modules) - 1 < int(line) < -1:
                        raise ValueError

                    if int(line) == -1:
                        self.menu_level = self.MENU_MAIN
                        self.current_option = None
                        self.context = None
                        self.print_main_menu()
                        return

                    self.show_module(int(line))
                except (ValueError, IndexError):
                    self.print_module_list_menu()
            elif self.menu_level == self.MENU_MODULE:
                try:
                    if len(self.module_menu_items) - 1 < int(line) < -1:
                        raise ValueError

                    if int(line) == -1:
                        self.menu_level = self.MENU_MODULE_LIST
                        self.current_option = None
                        self.context = None
                        self.print_module_list_menu()
                        return

                    # Call the matching function
                    self.module_menu_items[int(line)].values()[0](line)
                except (ValueError, IndexError):
                    self.print_module_menu()
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

    def print_module_list_menu(self):
        os.system('clear')
        msg(self._colorize('\n' + self.header, 'pink'))
        msg(self._colorize('version 0.1', 'green'))

        modules = self.module_community.get_modules_from_catalog()

        msg(self._colorize(str(len(modules)) + " modules found:", 'blue'))

        msg(self._colorize("[-1] ", 'blue') + self._colorize("Return to previous menu", 'green'))

        for module in modules:
            msg(self._colorize("[" + str(modules.index(module)) + "] ", 'blue') + self._colorize(str(module), 'green'))

    def print_module_menu(self):
        os.system('clear')
        msg(self._colorize('\n' + self.header, 'pink'))
        msg(self._colorize('version 0.1', 'green'))

        module = self.module_community.get_module_from_catalog(self.context.id)  # type: Module

        msg(self._colorize("Creator: " + str(hexlify(module.id.creator)), 'green'))
        msg(self._colorize("Content Hash: " + str(module.id.content_hash), 'green'))
        msg(self._colorize("Name: " + str(module.name), 'green'))
        msg(self._colorize("Votes: " + str(module.votes), 'green'))

        msg(self._colorize("[-1] ", 'blue') + self._colorize("Return to previous menu", 'green'))

        for item in self.module_menu_items:
            msg(self._colorize("[" + str(self.module_menu_items.index(item)) + "] ", 'blue') + item.keys()[0])

    def reset(self):
        self.menu_level = self.MENU_MAIN
        self.current_option = self.OPTION_NONE
        self.context = None
        self.print_main_menu()

    def create_test_module(self, line):
        self.module_community.create_module_test()

        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def create_module_setup(self, line):
        self.current_option = self.create_module
        msg(self._colorize("Press enter module package name", 'green'))

    def create_module(self, line):
        msg(self._colorize("module name: " + line, 'blue'))
        self.module_community.create_module(line)

        self.current_option = None
        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def show_modules(self, line):
        self.menu_level = self.MENU_MODULE_LIST
        self.print_module_list_menu()

    def show_module(self, line):
        modules = self.module_community.get_modules_from_catalog()
        index = int(line)

        msg("Number of modules retrieved: " + str(len(modules)))

        self.menu_level = self.MENU_MODULE
        self.context = modules[index]  # type: Module
        self.print_module_menu()

    def download_module(self, line):
        self.module_community.download_module(self.context.id)

        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def run_module(self, line):
        self.module_community.run_module(self.context.id)

        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def vote_module(self, line):
        self.module_community.vote_module(self.context.id)

        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def exit(self, line):
        self.service.stop()
