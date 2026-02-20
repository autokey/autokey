#  Copyright (C) 2026  David King <dave@daveking.com>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License,
#  version 2, as published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License,
#  version 2, along with this program; if not, see 
#  <https://www.gnu.org/licenses/old-licenses/gpl-2.0.html>.
#
#####################################################################

#  When running under Wayland, check to be sure we're running under a supported
#  desktop environment and that the prereqs that desktop environment needs are 
#  in place.

import grp
import os
import subprocess

try:
    logger = __import__("autokey.logger").logger.get_logger(__name__)
except Exception:
    #  For standalone testing
    import logging
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    logger = logging.getLogger(__name__)

def waylandChecks():

    try:
        #  We only do this stuff when running under Wayland
        if os.environ['XDG_SESSION_TYPE'] != "wayland":
            return True

        #  Check that we're running on a supported desktop environment
        #  dlk3 for future reference, the check for KDE on Ubunntu is os.environ['KDE_FULL_SESSION']
        if os.environ['XDG_SESSION_DESKTOP'] == 'gnome' or 'GNOME_DESKTOP_SESSION_ID' in os.environ:
            logger.debug(f"waylandChecks() found AutoKey running under a supported desktop environment")
        else:
            logger.debug(f"waylandChecks() found AutoKey running under an unsupported desktop environment, displaying popup.")
            __show_unsupported_desktop_popup()
            return False
    except Exception as e:
        logger.exception('Unexpected exception in waylandChecks() while examining environment variables')
        return False

    #  Do we show popup message?
    show_popup = False

    #  Gnome check: is the Gnome Shell extension present?
    ext_id = 'autokey-gnome-extension@autokey'
    try:
        proc = subprocess.run(f'gnome-extensions info {ext_id}', shell=True, capture_output=True, check=True)
        if 'Enabled: Yes' in proc.stdout.decode('utf-8'):
            logger.debug('waylandChecks() found the AutoKey Gnome Shell extension')
        else:
            logger.debug('waylandChecks() found the AutoKey Gnome Shell extension but it is disabled.  Attempting to enable it.')
            subprocess.run(f'gnome-extensions enable {ext_id}', shell=True, capture_output=True, check=True)
    except Exception:
        logger.critical('waylandChecks() did not find the AutoKey Gnome Shell extension, displaying popup')
        show_popup = True

    #  Gnome check: is the user in the input user group"
    group = 'input'
    user = os.getlogin()
    input_group = grp.getgrnam(group)
    if user in input_group.gr_mem or os.geteuid() == 0:
        logger.debug(f'waylandChecks() found the "{user}" userid in the "{group}" user group.')
    else:
        logger.critical(f'waylandChecks() did not find the "{user}" userid in the "{group}" user group, displaying popup.')
        show_popup = True

    #  Gnome check: do we have write access to the /dev/uinput device?
    if os.access('/dev/uinput', os.W_OK):
        logger.debug(f'waylandChecks() found write access to the /dev/uinput device')
    else:
        logger.critical(f'waylandChecks() did not find write access to the /dev/uinput device')
        show_popup = True

    #  If there was a problem, throw up a popup box telling them what to do
    if show_popup:
        #  This is Gnome-specific, other DTEs added in the future may need 
        #  different messages
        title = 'AutoKey System Configuration Needed'
        message = f'Your user id is not configured to run AutoKey under Waland.  If this is your <b>first time</b> running AutoKey, try <b>rebooting</b> your system and starting AutoKey again.  Otherwise, try entering these two commands, then rebooting:<br /><br />sudo usermod -a -G "{group}" "{user}"<br /><br />gnome-extensions install --force /usr/share/autokey/gnome-shell-extension/autokey-gnome-extension@autokey.shell-extension.zip'
        __show_popup(title, message)
        return False

    return True

def __show_unsupported_desktop_popup():
        dte = os.environ['XDG_SESSION_DESKTOP']
        title = 'Unsupported Desktop Environment'
        message = f'AutoKey does not support the "{dte}" desktop environment on a system that uses the Wayland window manageri like this one. The "{dte}" desktop environment is supported under X11, but not here under Wayland.  Future development may remove this restriction, please stay tuned.'
        __show_popup(title, message)

#  Show popup using kdialog, if it's installed, or zenity, otherwise write the
#  message to autokey.log
def __show_popup(title, message):
        try:
            subprocess.run(f"kdialog --error '{message}' --title '{title}'", shell=True, check=True)
        except Exception:
            try:

                subprocess.run(f"zenity --error --title='{title}' --text='{message.replace('<br />', '\n')}'", shell=True, check=True)
            except Exception:
                logger.critical(message)

#  For testing purposes
if __name__ == '__main__':
    if not waylandChecks():
        print('waylandChecks() returned False')
