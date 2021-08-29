#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2021 BlueDrink9
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gettext
# Must be done before any autokey imports, to localise any module setup strings.
gettext.install("autokey")

import sys

from autokey.autokey_app import AutokeyApplication
from autokey.abstract_ui import AutokeyUIInterface
import autokey.argument_parser
from . import common


logger = __import__("autokey.logger").logger.get_logger(__name__)

# TODO: this _ named function is initialised by gettext.install(), which is for
# localisation. It marks the string as a candidate for translation, but I don't
# know what else.
PROGRAM_NAME = _("AutoKey")
DESCRIPTION = _("Desktop automation utility")
COPYRIGHT = _("(c) 2008-2011 Chris Dekter")
common.USED_UI_TYPE = "headless"


class Application(AutokeyApplication, AutokeyUIInterface):
    """
    Main application class; starting and stopping of the application is controlled
    from here.
    """

    def __init__(self):
        autokey.common.USED_UI_TYPE = "headless"
        args = autokey.argument_parser.parse_args()
        super().__init__(args, UI=self)

        try:
            self.initialise(args)
        except Exception as e:
            self.show_error_dialog(_("Fatal error starting AutoKey.\n") + str(e))
            logger.error("Fatal error starting AutoKey: " + str(e))
            sys.exit(1)

    def initialise(self, configure):

        self.notifier = None
        self.configWindow = None

    def shutdown(self):
        """
        Shut down cli application.
        """
        logger.info("Shutting down")
        super().autokey_shutdown()
        logger.debug("All shutdown tasks complete... quitting")
        sys.exit(0)

    # def notify_error(self, error: autokey.model.script.ScriptErrorRecord):
    #     """
    #     Show an error notification popup.

    #     @param error: The error that occurred in a Script
    #     """
    #     message = "The script '{}' encountered an error".format(error.script_name)
    #     self.notifier.notify_error(message)
    #     if self.configWindow is not None:
    #         self.configWindow.set_has_errors(True)

    def show_configure(self):
        """
        Here to prevent blocking if another autokey instance tries to open.
        """
        logger.warning("Dbus asked autokey to show configure window, but we are running in headless mode so have no configure window.")
        return


    def show_error_dialog(self, message, details=None):
        """
        Abstract method to be implemented. Normally convenience method for
        showing a dialogue, but for CLI can just print the error for now.
        """
        print(
            """

            === Autokey Error Dialog ===
            {}
            === Autokey Error Dialog ===

            """.format(message)
        )


import faulthandler
faulthandler.enable()

def main():
    _ = Application()

if __name__ == '__main__':
    main()
