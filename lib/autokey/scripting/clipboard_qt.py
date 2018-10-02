import threading

from PyQt5.QtGui import QClipboard
from PyQt5.QtWidgets import QApplication


class QtClipboard:
    """
    Read/write access to the X selection and clipboard - QT version
    """

    def __init__(self, app):
        self.clipBoard = QApplication.clipboard()
        self.app = app

    def fill_selection(self, contents):
        """
        Copy text into the X selection

        Usage: C{clipboard.fill_selection(contents)}

        @param contents: string to be placed in the selection
        """
        self.__execAsync(self.__fillSelection, contents)

    def __fillSelection(self, string):
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
        self.text = self.clipBoard.text(QClipboard.Clipboard)
        self.sem.release()

    def __execAsync(self, callback, *args):
        self.sem = threading.Semaphore(0)
        self.app.exec_in_main(callback, *args)
        self.sem.acquire()
