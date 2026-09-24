"""
QtClipboard Functions
"""

import threading

from PyQt5.QtGui import QClipboard, QImage
from PyQt5.QtWidgets import QApplication
from autokey.scripting.abstract_clipboard import AbstractClipboard

import autokey.common
from pathlib import Path

logger = __import__("autokey.logger").logger.get_logger(__name__)

class QtClipboard(AbstractClipboard):
    """
    Read/write access to the X selection and clipboard - QT version
    """

    def __init__(self, app=None):
        """
        Initialize the Qt version of the clipboard

        Usage: Called when QtClipboard is imported.

        :param app: refers to the application instance
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

        self._klipper_interface = None
        """
        Lazily-created connection to KDE's klipper D-Bus service, used
        instead of QClipboard.setText() on KDE Wayland. See
        _use_klipper_for_clipboard().
        """

    def _use_klipper_for_clipboard(self) -> bool:
        """
        On KDE Wayland, QClipboard.setText(..., QClipboard.Clipboard) is a
        normal Wayland client request that KWin silently drops: AutoKey is
        a background daemon with no focused surface of its own when a
        hotkey fires in another application, so it has no input-event
        serial to offer for wl_data_device.set_selection(). Confirmed live:
        the call returns normally and QClipboard reads its own value back
        afterward, but an external reader (xclip, or the very application
        the paste is meant to land in) never sees the change.

        klipper (KDE's clipboard manager, a standard D-Bus service present
        on any Plasma session, no extension install needed) can set the
        clipboard on our behalf instead, because it is not an ordinary
        Wayland client making that same claim. See
        _get_klipper_interface().

        This does not apply to fill_selection()/PRIMARY: klipper only
        manages the CLIPBOARD selection.
        """
        return autokey.common.SESSION_TYPE == "wayland" and autokey.common.DESKTOP == "KDE"

    def _get_klipper_interface(self):
        """
        Returns klipper's D-Bus interface, or None if it's not available.

        klipper is KDE's *default* clipboard manager, but not the only one
        a Plasma user can run -- klipper can be disabled, or replaced with
        an alternative (e.g. CopyQ). Neither AutoKey nor this fix installs
        or requires klipper the way GNOME's path requires AutoKey's own
        Shell extension, so unlike that path, a missing klipper here isn't
        a setup error to report loudly -- it's an expected configuration
        for some users. connecting to a D-Bus service that isn't running
        raises (confirmed live: pydbus/GLib raise
        org.freedesktop.DBus.Error.ServiceUnknown), so this is cached after
        the first attempt (both success and failure) to avoid retrying a
        known-absent service on every single clipboard operation.
        """
        if self._klipper_interface is None:
            from pydbus import SessionBus
            try:
                self._klipper_interface = SessionBus().get("org.kde.klipper", "/klipper")
            except Exception as e:
                logger.warning(
                    "klipper D-Bus service unavailable (%s) -- falling back to Qt's own "
                    "clipboard API, which is known not to sync reliably with other "
                    "applications on KDE Wayland (see _use_klipper_for_clipboard()). "
                    "If you use an alternative clipboard manager, AutoKey does not "
                    "currently integrate with it directly.", e
                )
                self._klipper_interface = False  # sentinel: don't retry every call
        return self._klipper_interface or None

    def fill_selection(self, contents):
        """
        Copy text into the selection

        Usage: C{clipboard.fill_selection(contents)}

        :param contents: string to be placed in the selection
        """
        self.__execAsync(self.__fillSelection, contents)

    @property
    def clipBoard(self):
        # Fetching this once in __init__ doesn't work: IoMediator (and
        # therefore this Clipboard) is constructed during Service.start(),
        # which happens before QApplication is fully initialised, so
        # QApplication.clipboard() at that point isn't a live, working
        # reference. Fetch it fresh on every use instead.
        return QApplication.clipboard()

    def __fillSelection(self, string):
        """
        Backend for the C{fill_selection} method

        Sets the selection text to the C{string} value

        :param string: Value to change the selection to
        """
        self.clipBoard.setText(string, QClipboard.Selection)
        if self.app:
            self.sem.release()

    def get_selection(self):
        """
        Read text from the selection

        Usage: C{clipboard.get_selection()}

        :return: text contents of the mouse selection
        :rtype: C{str}
        """
        self.__execAsync(self.__getSelection)
        return str(self.text)

    def __getSelection(self):
        self.text = self.clipBoard.text(QClipboard.Selection)
        if self.app:
            self.sem.release()

    def fill_clipboard(self, contents):
        """
        Copy text onto the clipboard

        Usage: C{clipboard.fill_clipboard(contents)}

        :param contents: string to be placed in the selection

        On KDE Wayland, routed through klipper's D-Bus service instead of
        Qt's own clipboard API -- see _use_klipper_for_clipboard(). klipper's
        call is a plain synchronous D-Bus round trip, not a Qt GUI
        operation, so it does not need __execAsync's main-thread dispatch.
        If klipper isn't available (not running, or replaced by another
        clipboard manager -- see _get_klipper_interface()), falls back to
        Qt's own clipboard API, same as pre-fix behavior.
        """
        if self._use_klipper_for_clipboard():
            klipper = self._get_klipper_interface()
            if klipper is not None:
                klipper.setClipboardContents(contents)
                return
        self.__execAsync(self.__fillClipboard, contents)

    def set_clipboard_image(self, path):
        """
        Set clipboard to image

        Usage: C{clipboard.set_clipboard_image(path)}

        :param path: Path to image file
        :raise OSError: If path does not exist
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
        if self.app:
            self.sem.release()

    def get_clipboard(self):
        """
        Read text from the clipboard

        Usage: C{clipboard.get_clipboard()}

        :return: text contents of the clipboard
        :rtype: C{str}

        On KDE Wayland, routed through klipper -- see
        _use_klipper_for_clipboard(). QClipboard.text(QClipboard.Clipboard)
        has the same underlying problem as the write side, just less visible:
        it returns without error but can read back stale/empty content
        instead of what another client (e.g. xclip, or a real user's copy)
        actually currently holds. Confirmed live: reading immediately after
        an external xclip set returned '' here while klipper's own
        getClipboardContents() correctly returned the just-set value. Falls
        back to Qt's own clipboard API if klipper isn't available -- see
        _get_klipper_interface().
        """
        if self._use_klipper_for_clipboard():
            klipper = self._get_klipper_interface()
            if klipper is not None:
                return str(klipper.getClipboardContents())
        self.__execAsync(self.__getClipboard)
        return str(self.text)

    def __getClipboard(self):
        """
        Backend for the C{get_clipboard} method

        Stores the value of the clipboard into the C{self.text} variable
        """
        self.text = self.clipBoard.text(QClipboard.Clipboard)
        if self.app:
            self.sem.release()

    def __execAsync(self, callback, *args):
        """
        Backend to execute methods asynchronously in Qt.
        If clipboard instance was created without being passed a QtApp instance,
        executes synchronously instead.
        """
        if self.app:
            self.sem = threading.Semaphore(0)
            self.app.exec_in_main(callback, *args)
            self.sem.acquire()
        else:
            return callback(*args)
