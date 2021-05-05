"""
QtClipboard Functions
"""

import threading

from PyQt5.QtGui import QClipboard, QImage
from PyQt5.QtWidgets import QApplication

from pathlib import Path


class QtClipboard:
    """
    Read/write access to the X selection and clipboard - QT version
    """

    def __init__(self, app):
        """
        Initialize the Qt version of the Clipboard

        Usage: Called when QtClipboard is imported.

        @param app: refers to the application instance
        """
        self.clipBoard = QApplication.clipboard()
        """
        Refers to the Qt clipboard object
        """

        self.app = app
        """
        Refers to the application instance
        """

        self.text = None
        """
        Used to temporarily store the value of the selection or clipboard
        """

        self.sem = None
        """
        Qt semaphore object used for asynchronous method execution
        """

    def fill_selection(self, contents):
        """
        Copy text into the X selection

        Usage: C{clipboard.fill_selection(contents)}

        @param contents: string to be placed in the selection
        """
        self.__execAsync(self.__fillSelection, contents)

    def __fillSelection(self, string):
        """
        Backend for the C{fill_selection} method

        Sets the selection text to the C{string} value

        @param string: Value to change the selection to
        """
        self.clipBoard.setText(string, QClipboard.Selection)
        self.sem.release()

    def get_selection(self):
        """
        Read text from the X selection

        Usage: C{clipboard.get_selection()}

        @return: text contents of the mouse selection
        @rtype: C{str}
        """
        self.__execAsync(self.__getSelection)
        return str(self.text)

    def __getSelection(self):
        self.text = self.clipBoard.text(QClipboard.Selection)
        self.sem.release()

    def fill_clipboard(self, contents):
        """
        Copy text into the clipboard

        Usage: C{clipboard.fill_clipboard(contents)}

        @param contents: string to be placed in the selection
        """
        self.__execAsync(self.__fillClipboard, contents)

    def set_clipboard_image(self, path):
        """
        Set clipboard to image

        Usage: C{clipboard.set_clipboard_image(path)}

        @param path: Path to image file
        @raise OSError: If path does not exist
        """
        self.__execAsync(self.__set_clipboard_image, path)

    def __set_clipboard_image(self, path):
        image_path = Path(path).expanduser()
        if image_path.exists():
            copied_image = QImage()
            copied_image.load(str(image_path))
            self.clipBoard.setImage(copied_image)
        else:
            raise OSError

    def __fillClipboard(self, string):
        self.clipBoard.setText(string, QClipboard.Clipboard)
        self.sem.release()

    def get_clipboard(self):
        """
        Read text from the clipboard

        Usage: C{clipboard.get_clipboard()}

        @return: text contents of the clipboard
        @rtype: C{str}
        """
        self.__execAsync(self.__getClipboard)
        return str(self.text)

    def __getClipboard(self):
        """
        Backend for the C{get_clipboard} method

        Stores the value of the clipboard into the C{self.text} variable
        """
        self.text = self.clipBoard.text(QClipboard.Clipboard)
        self.sem.release()

    def __execAsync(self, callback, *args):
        """
        Backend to execute methods asynchronously in Qt
        """
        self.sem = threading.Semaphore(0)
        self.app.exec_in_main(callback, *args)
        self.sem.acquire()
