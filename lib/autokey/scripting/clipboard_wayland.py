# Copyright (C) 2024 AutoKey Contributors
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

"""
Implementation of the clipboard API functions on a Wayland system.
Uses wl-clipboard (wl-copy, wl-paste) for clipboard operations.
"""

import subprocess
import shutil

logger = __import__("autokey.logger").logger.get_logger(__name__)


class WaylandClipboard:
    """
    Read write access to the Wayland desktop using the wl-clipboard utility.
    """
    
    def __init__(self, app=None):
        """
        Initialize the Wayland version of the clipboard API.
        """
        self.app = app
        self._wl_copy = shutil.which('wl-copy')
        self._wl_paste = shutil.which('wl-paste')
        
        if not self._wl_copy or not self._wl_paste:
            logger.warning("wl-clipboard not found. Clipboard operations may not work on Wayland.")
            logger.warning("Install wl-clipboard package for Wayland clipboard support.")
    
    def fill_clipboard(self, contents: str):
        """
        Copy text into the clipboard.

        Usage: C{clipboard.fill_clipboard(contents)}

        :param contents: string to be placed in the clipboard
        """
        if not self._wl_copy:
            logger.warning("wl-copy not available")
            return
            
        try:
            subprocess.run([self._wl_copy, contents], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.exception('Unexpected error running wl-copy program. AutoKey continues.')
        except FileNotFoundError:
            logger.warning("wl-copy not found. Install wl-clipboard package.")
            
    def get_clipboard(self) -> str:
        """
        Read text from the clipboard.

        Usage: C{clipboard.get_clipboard()}

        :return: text contents of the clipboard
        :rtype: C{str}
        """
        if not self._wl_paste:
            logger.warning("wl-paste not available")
            return ""
            
        try:
            proc = subprocess.run([self._wl_paste], check=True, capture_output=True)
            if proc.stdout:
                return proc.stdout.decode('utf-8', errors='replace').rstrip('\n\r')
            else:
                logger.warning("No content available from the clipboard")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                logger.warning("No content available from the clipboard")
                return ""
            logger.exception('Unexpected error running wl-paste program. AutoKey continues.')
        except FileNotFoundError:
            logger.warning("wl-paste not found. Install wl-clipboard package.")
            
        return ""

    def fill_selection(self, contents: str):
        """
        Copy text into the selection (primary clipboard).
        
        Usage: C{clipboard.fill_selection(contents)}

        :param contents: string to be placed in the selection
        """
        if not self._wl_copy:
            logger.warning("wl-copy not available")
            return
            
        try:
            subprocess.run([self._wl_copy, '--primary', contents], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.exception('Unexpected error running wl-copy program. AutoKey continues.')
        except FileNotFoundError:
            logger.warning("wl-copy not found. Install wl-clipboard package.")

    def get_selection(self) -> str:
        """
        Read text from the X selection (primary clipboard).
        The selection refers to the currently highlighted text.

        Usage: C{clipboard.get_selection()}

        :return: text contents of the mouse selection
        :rtype: C{str}
        """
        if not self._wl_paste:
            logger.warning("wl-paste not available")
            return ""
            
        try:
            proc = subprocess.run([self._wl_paste, '--primary'], check=True, capture_output=True)
            if proc.stdout:
                return proc.stdout.decode('utf-8', errors='replace').rstrip('\n\r')
            else:
                logger.warning("No content selected on desktop")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                logger.warning("No content selected on desktop")
                return ""
            logger.exception('Unexpected error running wl-paste program. AutoKey continues.')
        except FileNotFoundError:
            logger.warning("wl-paste not found. Install wl-clipboard package.")
            
        return ""