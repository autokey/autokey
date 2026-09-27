# Copyright (C) 2011 Chris Dekter

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging
from unittest.mock import MagicMock, patch

import hamcrest as hm
import pytest

import autokey
# Needs to be set before importing scripting
autokey.common.USED_UI_TYPE = "headless"
import autokey.scripting.clipboard_pyperclip as clipboard_pyperclip
import autokey.sys_interface.clipboard
from autokey.scripting.clipboard_pyperclip import PyperclipClipboard

logger = __import__("autokey.logger").logger.get_logger(__name__)


def get_errors_in_log(caplog):
    return [record for record in caplog.get_records('call') if record.levelno >= logging.ERROR]


def test_module_import_eagerly_binds_pyperclip_backend():
    """
    Regression test: pyperclip.copy()/paste() are lazy stubs until first
    called, and that stub's signature doesn't accept the primary= kwarg
    fill_selection()/get_selection() pass -- confirmed live, this crashes
    with a TypeError if a SELECTION-mode phrase is the first clipboard
    operation a real AutoKey process ever performs, before any CB_CTRL_V
    phrase has run plain copy()/paste() to bind the real backend first.
    Importing this module must bind the real backend immediately so
    fill_selection()/get_selection() are safe to call first.
    """
    hm.assert_that(clipboard_pyperclip.pyperclip.copy.__name__, hm.not_(hm.equal_to("lazy_load_stub_copy")))
    hm.assert_that(clipboard_pyperclip.pyperclip.paste.__name__, hm.not_(hm.equal_to("lazy_load_stub_paste")))


def test_fill_clipboard_calls_pyperclip_copy():
    clipboard = PyperclipClipboard()
    with patch.object(clipboard_pyperclip.pyperclip, "copy") as mock_copy:
        clipboard.fill_clipboard("test contents")
        mock_copy.assert_called_once_with("test contents")


def test_get_clipboard_calls_pyperclip_paste():
    clipboard = PyperclipClipboard()
    with patch.object(clipboard_pyperclip.pyperclip, "paste", return_value="test contents") as mock_paste:
        hm.assert_that(clipboard.get_clipboard(), hm.equal_to("test contents"))
        mock_paste.assert_called_once_with()


def test_get_clipboard_returns_empty_string_and_warns_when_empty(caplog):
    clipboard = PyperclipClipboard()
    with patch.object(clipboard_pyperclip.pyperclip, "paste", return_value=""):
        with caplog.at_level(logging.WARNING):
            hm.assert_that(clipboard.get_clipboard(), hm.equal_to(""))
    hm.assert_that(
        any("clipboard" in record.message.lower() for record in caplog.records),
        hm.equal_to(True)
    )


def test_fill_selection_uses_primary_kwarg():
    """
    fill_selection() must set the PRIMARY selection, not the CLIPBOARD --
    pyperclip's public copy()/paste() default to CLIPBOARD, and reach
    PRIMARY only via the primary=True kwarg.
    """
    clipboard = PyperclipClipboard()
    with patch.object(clipboard_pyperclip.pyperclip, "copy") as mock_copy:
        clipboard.fill_selection("selected text")
        mock_copy.assert_called_once_with("selected text", primary=True)


def test_get_selection_uses_primary_kwarg():
    clipboard = PyperclipClipboard()
    with patch.object(clipboard_pyperclip.pyperclip, "paste", return_value="selected text") as mock_paste:
        hm.assert_that(clipboard.get_selection(), hm.equal_to("selected text"))
        mock_paste.assert_called_once_with(primary=True)


def test_get_selection_returns_empty_string_and_warns_when_empty(caplog):
    clipboard = PyperclipClipboard()
    with patch.object(clipboard_pyperclip.pyperclip, "paste", return_value=None):
        with caplog.at_level(logging.WARNING):
            hm.assert_that(clipboard.get_selection(), hm.equal_to(""))
    hm.assert_that(
        any("selection" in record.message.lower() for record in caplog.records),
        hm.equal_to(True)
    )


def test_set_clipboard_image_raises_oserror_for_missing_file():
    clipboard = PyperclipClipboard()
    with pytest.raises(OSError):
        clipboard.set_clipboard_image("/no/such/file.png")


def test_set_clipboard_image_headless_logs_error_and_does_not_raise(tmp_path, caplog):
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"not really a png, contents are unused by this test")
    clipboard = PyperclipClipboard()
    original_ui_type = autokey.common.USED_UI_TYPE
    try:
        autokey.common.USED_UI_TYPE = "headless"
        with caplog.at_level(logging.ERROR):
            clipboard.set_clipboard_image(str(image_path))
    finally:
        autokey.common.USED_UI_TYPE = original_ui_type
    hm.assert_that(len(get_errors_in_log(caplog)), hm.greater_than(0))


def test_set_clipboard_image_gtk_uses_gtk_clipboard(tmp_path):
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"not really a png, contents are unused by this test")
    clipboard = PyperclipClipboard()
    original_ui_type = autokey.common.USED_UI_TYPE
    try:
        autokey.common.USED_UI_TYPE = "GTK"
        with patch("gi.repository.Gtk", create=True) as mock_gtk, \
             patch("gi.repository.Gdk", create=True) as mock_gdk:
            mock_pixbuf_image = MagicMock()
            mock_gtk.Image.new_from_file.return_value = mock_pixbuf_image
            clipboard.set_clipboard_image(str(image_path))
            mock_gtk.Image.new_from_file.assert_called_once_with(str(image_path))
            mock_gtk.Clipboard.get.return_value.set_image.assert_called_once_with(
                mock_pixbuf_image.get_pixbuf.return_value
            )
    finally:
        autokey.common.USED_UI_TYPE = original_ui_type


def test_set_clipboard_image_qt_runs_synchronously_without_app(tmp_path):
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"not really a png, contents are unused by this test")
    clipboard = PyperclipClipboard(app=None)
    original_ui_type = autokey.common.USED_UI_TYPE
    try:
        autokey.common.USED_UI_TYPE = "QT"
        with patch("PyQt5.QtGui.QImage") as mock_qimage_class, \
             patch("PyQt5.QtWidgets.QApplication") as mock_qapp_class:
            clipboard.set_clipboard_image(str(image_path))
            mock_qimage_class.return_value.load.assert_called_once_with(str(image_path))
            mock_qapp_class.clipboard.return_value.setImage.assert_called_once_with(
                mock_qimage_class.return_value
            )
    finally:
        autokey.common.USED_UI_TYPE = original_ui_type


def test_set_clipboard_image_qt_dispatches_through_app_exec_in_main(tmp_path):
    """
    Regression guard: unlike text fill/get (which pyperclip handles via an
    independent subprocess, needing no toolkit thread marshaling), image
    setting still goes through Qt's own clipboard API directly, so it must
    still be dispatched onto the toolkit main thread when an app instance
    (with a real event loop) is available -- matching the old QtClipboard's
    behavior.
    """
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"not really a png, contents are unused by this test")
    mock_app = MagicMock()

    def immediately_run(callback, *args):
        callback(*args)

    mock_app.exec_in_main.side_effect = immediately_run
    clipboard = PyperclipClipboard(app=mock_app)
    original_ui_type = autokey.common.USED_UI_TYPE
    try:
        autokey.common.USED_UI_TYPE = "QT"
        with patch("PyQt5.QtGui.QImage"), patch("PyQt5.QtWidgets.QApplication"):
            clipboard.set_clipboard_image(str(image_path))
            mock_app.exec_in_main.assert_called_once()
    finally:
        autokey.common.USED_UI_TYPE = original_ui_type


def test_sys_interface_clipboard_wraps_pyperclip_clipboard():
    """
    autokey.sys_interface.clipboard.Clipboard (used by iomediator for Phrase
    expansion, not the scripting API's own Clipboard) wraps whatever
    autokey.scripting.Clipboard resolves to via its text/selection
    properties. With clipboard_pyperclip.py wired in as that Clipboard for
    every front end, it must wrap PyperclipClipboard.
    """
    clipboard = autokey.sys_interface.clipboard.Clipboard()
    hm.assert_that(clipboard.cb, hm.instance_of(PyperclipClipboard))
    with patch.object(clipboard_pyperclip.pyperclip, "copy") as mock_copy:
        clipboard.text = "test contents"
        mock_copy.assert_called_once_with("test contents")
