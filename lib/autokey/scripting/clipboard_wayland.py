#  Copyright (C) 2026 David King <dave@daveking.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#####################################################################

"""
Implementation of the clipboard API functions on a Wayland system
"""

try:
    from .abstract_clipboard import AbstractClipboard
except:
    #  For standalone testing
    pass

import subprocess
import pathlib
import re

try:
    logger = __import__("autokey.logger").logger.get_logger(__name__)
except Exception:
    #  For standalone testing
    import logging
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    logger = logging.getLogger(__name__)

# Swap these lines for standalone testing:
#class WaylandClipboard():
class WaylandClipboard(AbstractClipboard):
    """
    Read write access to the Wayland desktop using the wl-clipboard utility
    """
    def __init__(self, app=None):
        """
        Initialize the Wayland version of the clipboard API

        Usage: Called when WaylandClipboard is imported

        :param app: refers to the application instance
        """
        self.app = app
        
    def fill_clipboard(self, contents: str):
        """
        Copy text into the clipboard

        Usage: C{clipboard.fill_clipboard(contents)}

        :param contents: string to be placed in the selection
        """
        try:
            subprocess.run(['wl-copy', contents], check=True)
        except subprocess.CalledProcessError:
            logger.exception('Unexpected error running wl-copy program.  AutoKey continues.')
        return
        
    def get_clipboard(self):
        """
        Read text from the clipboard

        Usage: C{clipboard.get_clipboard()}

        :return: text contents of the clipboard
        :rtype: C{str}, or C{bytearray} on Python >= 3.13
        """
        try:
            proc = subprocess.run(['wl-paste'], check=True, capture_output=True)
            if proc.stdout is not None:
                return re.sub(b'[\r\n]*$', b'', proc.stdout)
            else: 
                logger.warning("No content available from the clipboard")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                logger.warning("No content available from the clipboard")
                return ""
            logger.exception('Unexpected error running wl-copy program.  AutoKey continues.')
        return ""

    def fill_selection(self, contents: str):
        """
        Copy text into the selection
        
        Usage: C{clipboard.fill_selection(contents)}

        :param contents: string to be placed in the selection
        """
        try:
            subprocess.run(['wl-copy', '--primary', contents], check=True)
        except subprocess.CalledProcessError:
            logger.exception('Unexpected error running wl-copy program.  AutoKey continues.')
        return

    def get_selection(self):
        """
        Read text from the X selection
        The selection refers to the currently highlighted text.

        **Notice:**  This is not possible under Wayland.

        Usage: C{clipboard.get_selection()}

        :return: text contents of the mouse selection
        :rtype: C{str}
        """
        try:
            proc = subprocess.run(['wl-paste', '--primary'], check=True, capture_output=True)
            if proc.stdout is not None:
                return re.sub(b'[\r\n]*$', b'', proc.stdout)
            else: 
                logger.warning("No content selected on desktop")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                logger.warning("No content selected on desktop")
                return ""
            logger.exception('Unexpected error running wl-copy program.  AutoKey continues.')
        return ""

    def set_clipboard_image(self, path: str):
        """
        Set clipboard to image

        Usage: C{clipboard.set_clipboard_image(path)}

        :param path: Path to image file
        :raise OSError: If path does not exist
        """
        try:
            image_file = pathlib.Path(path).expanduser()
            if image_file.exists():
                subprocess.run(f'wl-copy <{image_file}', shell=True, check=True)
        except subprocess.CalledProcessError:
            logger.exception('Unexpected error running wl-copy program.  AutoKey continues.')
        return

#  For standalone testing
if __name__ == '__main__':
    import datetime
    
    logger.debug('Instantiating clipboard')
    clipboard = WaylandClipboard()

    logger.debug('Testing the regular clipboard')
    logger.debug(f'\tThe clipboard\'s current content = "{clipboard.get_clipboard()}"')   
    test_content = f'The current date and time are {datetime.datetime.now()}'
    logger.debug('\tPushing test string onto clipboard')
    clipboard.fill_clipboard(test_content)
    logger.debug('\tPulling text from clipboard')
    result = clipboard.get_clipboard()
    if result == test_content:
        logger.debug('\tThe text pulled matches the text pushed')
    else:
        logger.error(f'\tThe text pushed, "{test_content}", does not match the text pulled, "{result}"')
    logger.debug('\tPushing image file to clipboard, try creating a new image from the cliboard with a tool like GIMP')
    clipboard.set_clipboard_image('~/src/autokey-wayland/readthedocs/editconfig.jpg')

    logger.debug('Testing the primary (selection) clipboard')
    logger.debug(f'\tThe primary clipboard\'s current content = "{clipboard.get_selection()}"')   
    test_content = f'The current date and time are {datetime.datetime.now()}'
    logger.debug('\tPushing test string onto primary clipboard')
    clipboard.fill_selection(test_content)
    logger.debug('\tPulling text from primary clipboard')
    result = clipboard.get_selection()
    if result == test_content:
        logger.debug('\tThe text pulled matches the text pushed')
    else:
        logger.error(f'\tThe text pushed, "{test_content}", does not match the text pulled, "{result}"')
