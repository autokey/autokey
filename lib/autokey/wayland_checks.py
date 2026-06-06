#  When running under Wayland, check if running under a supported
#  desktop environment and that the prereqs that desktop environment needs are 
#  in place.

import getpass
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

def _is_kde():
    desktop = (
        os.environ.get('XDG_CURRENT_DESKTOP', '')
        + ' '
        + os.environ.get('XDG_SESSION_DESKTOP', '')
    ).lower()
    return 'kde' in desktop or 'plasma' in desktop


def _is_gnome():
    session_desktop = os.environ.get('XDG_SESSION_DESKTOP', '')
    return session_desktop.lower() == 'gnome' or 'GNOME_DESKTOP_SESSION_ID' in os.environ


def _check_uinput_group():
    """Check input group membership and /dev/uinput access. Returns True if popup needed."""
    show_popup = False
    group = 'input'
    user = getpass.getuser()
    try:
        input_group = grp.getgrnam(group)
    except KeyError:
        logger.critical(f'waylandChecks() did not find the "{group}" user group, displaying popup.')
        show_popup = True
    else:
        if user in input_group.gr_mem or os.geteuid() == 0:
            logger.debug(f'waylandChecks() found "{user}" in the "{group}" group.')
        else:
            logger.critical(f'waylandChecks() did not find "{user}" in the "{group}" group, displaying popup.')
            show_popup = True
    if os.access('/dev/uinput', os.W_OK):
        logger.debug('waylandChecks() found write access to /dev/uinput')
    else:
        logger.critical('waylandChecks() did not find write access to /dev/uinput')
        show_popup = True
    return show_popup


def waylandChecks():

    try:
        #  only do this stuff when running under Wayland
        if os.environ.get('XDG_SESSION_TYPE') != "wayland":
            return True

        if _is_gnome():
            logger.debug("waylandChecks() detected GNOME — running GNOME checks")
            return _gnome_checks()
        elif _is_kde():
            logger.debug("waylandChecks() detected KDE — running KDE checks")
            return _kde_checks()
        else:
            logger.debug("waylandChecks() detected an unsupported desktop, displaying popup.")
            __show_unsupported_desktop_popup()
            return False
    except Exception:
        logger.exception('Unexpected exception in waylandChecks()')
        return False


def _gnome_checks():
    show_popup = _check_uinput_group()

    ext_id = 'autokey-gnome-extension@autokey'
    try:
        proc = subprocess.run(f'gnome-extensions info {ext_id}', shell=True, capture_output=True, check=True)
        if 'Enabled: Yes' in proc.stdout.decode('utf-8'):
            logger.debug('waylandChecks() found the AutoKey GNOME Shell extension')
        else:
            logger.debug('AutoKey GNOME Shell extension disabled — attempting to enable it.')
            subprocess.run(f'gnome-extensions enable {ext_id}', shell=True, capture_output=True, check=True)
    except Exception:
        logger.critical('waylandChecks() did not find the AutoKey GNOME Shell extension, displaying popup')
        show_popup = True

    if show_popup:
        group = 'input'
        user = getpass.getuser()
        title = 'AutoKey System Configuration Needed'
        message = (
            f'Your user id is not configured to run AutoKey under Wayland.  '
            f'If this is your <b>first time</b> running AutoKey, try <b>rebooting</b> '
            f'your system and starting AutoKey again.  Otherwise, try entering these '
            f'two commands, then rebooting:<br /><br />'
            f'sudo usermod -a -G "{group}" "{user}"<br /><br />'
            f'gnome-extensions install --force '
            f'/usr/share/autokey/gnome-shell-extension/autokey-gnome-extension@autokey.shell-extension.zip'
        )
        __show_popup(title, message)
        return False
    return True


def _kde_checks():
    show_popup = _check_uinput_group()

    if show_popup:
        group = 'input'
        user = getpass.getuser()
        title = 'AutoKey System Configuration Needed'
        message = (
            f'Your user id is not configured to run AutoKey under KDE/Wayland.  '
            f'If this is your <b>first time</b> running AutoKey, try <b>rebooting</b> '
            f'your system and starting AutoKey again.  Otherwise, run this command '
            f'and reboot:<br /><br />'
            f'sudo usermod -a -G "{group}" "{user}"'
        )
        __show_popup(title, message)
        return False
    return True

def __show_unsupported_desktop_popup():
        dte = os.environ.get('XDG_SESSION_DESKTOP') or os.environ.get('DESKTOP_SESSION') or 'unknown'
        title = 'Unsupported Desktop Environment'
        message = f'AutoKey does not support the "{dte}" desktop environment on a system that uses the Wayland window manager like this one. The "{dte}" desktop environment is supported under X11, but not here under Wayland.  Future development may remove this restriction, please stay tuned.'
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
