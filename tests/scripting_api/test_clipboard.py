# Copyright (C) 2021 BlueDrink9

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
from datetime import datetime

import unittest
from unittest.mock import patch
import pytest
skip = pytest.mark.skip
import hamcrest as hm

import autokey
# Needs to be set before importing scripting
autokey.common.USED_UI_TYPE = "headless"
import autokey.scripting as api
import autokey.scripting.clipboard_gtk
import autokey.scripting.clipboard_qt
import autokey.scripting.clipboard_tkinter
import autokey.sys_interface.clipboard
from PyQt5.QtGui import QClipboard
from PyQt5.QtWidgets import QApplication

# QtClipboard's fallback path (Qt's own clipboard API) needs a live
# QApplication to back QApplication.clipboard() -- without one it returns
# None and raises AttributeError on use. The pre-existing test_qt_clipboard()
# doesn't actually exercise this (its "b.text = ..." is a plain attribute
# assignment, not a call through fill_clipboard() -- AbstractClipboard has
# no text property), so this was never needed until the klipper-fallback
# tests below, which do call fill_clipboard()/get_clipboard() for real.
_qapp = QApplication.instance() or QApplication([])

logger = __import__("autokey.logger").logger.get_logger(__name__)

def get_errors_in_log(caplog):
    errors = [record for record in caplog.get_records('call') if record.levelno >= logging.ERROR]
    return errors


@skip(reason="selection clipboard not implemented")
def  test_tkinter_selection_clipboard():
    # Note: this test does not test that the *system* clipboard is actually
    # filled, it just tests that the tk object clipboard is.
    #
    # Add current time to ensure fresh test string
    now = datetime.now()
    test_string = "this is the new clipboard contents {}".format(now)
    b = api.clipboard_tkinter.TkClipboard()
    b.fill_selection(test_string)
    hm.assert_that(
        b.get_selection(),
        hm.equal_to(test_string),
        "Selection clipboard is not the same as what it was filled with!"
    )

def  test_tkinter_clipboard():
    # Note: this test does not test that the *system* clipboard is actually
    # filled, it just tests that the tk object clipboard is.
    #
    # Add current time to ensure fresh test string
    now = datetime.now()
    test_string = "this is the new clipboard contents {}".format(now)
    b = api.clipboard_tkinter.TkClipboard()
    b.fill_clipboard(test_string)
    hm.assert_that(
        b.get_clipboard(),
        hm.equal_to(test_string),
        "Clipboard is not the same as what it was filled with!"
    )


def  test_tkinter_clipboard_from_interface():
    # Note: this test does not test that the *system* clipboard is actually
    # filled, it just tests that the tk object clipboard is.

    # Add current time to ensure fresh test string
    now = datetime.now()
    test_string = "this is the new clipboard contents {}".format(now)
    b = autokey.sys_interface.clipboard.Clipboard()
    # Need to overwrite to ensure it hasn't picked up a qtclipboard somewhere.
    b.cb = autokey.scripting.clipboard_tkinter.TkClipboard()
    # uses a setter that sets the clipboard rather than an internal variable
    b.text = test_string
    hm.assert_that(
        b.text,
        hm.equal_to(test_string),
        "Clipboard is not the same as what it was filled with!"
    )


def  test_gtk_clipboard():
    # Without a gtkapp, this clipboard does not work.
    # This test is purely to test the code path has no syntax errors.
    now = datetime.now()
    test_string = "this is the new clipboard contents {}".format(now)
    b = api.clipboard_gtk.GtkClipboard()
    # uses a setter that sets the clipboard rather than an internal variable
    b.text = test_string
    print(b.text)
    # hm.assert_that(
    #     b.text,
    #     hm.equal_to(test_string),
    #     "Clipboard is not the same as what it was filled with!"
    # )


def test_gtk_clipboard_routes_through_gnome_extension_on_gnome_wayland():
    """
    Regression test for a bug where GtkClipboard.fill_clipboard() always
    called Gtk.Clipboard.set_text() directly, which GNOME's Wayland
    compositor silently rejects for a background daemon like AutoKey (no
    input-event serial to offer -- confirmed live via WAYLAND_DEBUG=1
    tracing). On GNOME Wayland specifically, fill_clipboard() must instead
    call the AutoKey GNOME Shell extension's SetClipboardText D-Bus method,
    since the Shell itself is not an ordinary Wayland client and does not
    hit that rejection.
    """
    original_session_type = autokey.common.SESSION_TYPE
    original_desktop = autokey.common.DESKTOP
    try:
        autokey.common.SESSION_TYPE = "wayland"
        autokey.common.DESKTOP = "GNOME"
        clipboard = api.clipboard_gtk.GtkClipboard.__new__(api.clipboard_gtk.GtkClipboard)
        clipboard._gnome_clipboard_interface = unittest.mock.Mock()
        clipboard.fill_clipboard("test contents")
        clipboard._gnome_clipboard_interface.set_clipboard_text.assert_called_once_with("test contents")
    finally:
        autokey.common.SESSION_TYPE = original_session_type
        autokey.common.DESKTOP = original_desktop


def test_gtk_clipboard_does_not_use_gnome_extension_on_kde_or_x11():
    """
    This specific GTK-on-GNOME-Wayland check must not fire elsewhere: X11
    never had the rejection problem, and KDE's Qt-based clipboard has its
    own separate rejection problem worked around separately in
    clipboard_qt.py's _use_klipper_for_clipboard() -- not via the GNOME
    Shell extension, which doesn't exist under KDE.
    """
    original_session_type = autokey.common.SESSION_TYPE
    original_desktop = autokey.common.DESKTOP
    try:
        for session_type, desktop in [("wayland", "KDE"), ("x11", "GNOME"), (None, "")]:
            autokey.common.SESSION_TYPE = session_type
            autokey.common.DESKTOP = desktop
            clipboard = api.clipboard_gtk.GtkClipboard.__new__(api.clipboard_gtk.GtkClipboard)
            hm.assert_that(
                clipboard._use_gnome_extension_for_clipboard_set(),
                hm.equal_to(False),
                "Should not use the GNOME extension for session_type={!r}, desktop={!r}".format(
                    session_type, desktop)
            )
    finally:
        autokey.common.SESSION_TYPE = original_session_type
        autokey.common.DESKTOP = original_desktop


def  test_qt_clipboard():
    # Without a gtkapp, this clipboard does not work.
    # This test is purely to test the code path has no syntax errors.
    now = datetime.now()
    test_string = "this is the new clipboard contents {}".format(now)
    b = api.clipboard_qt.QtClipboard()
    # uses a setter that sets the clipboard rather than an internal variable
    b.text = test_string
    print(b.text)
    # hm.assert_that(
    #     b.text,
    #     hm.equal_to(test_string),
    #     "Clipboard is not the same as what it was filled with!"
    # )


def test_qt_clipboard_write_routes_through_klipper_on_kde_wayland():
    """
    Regression test for a bug where QtClipboard.fill_clipboard() always
    called QClipboard.setText(..., QClipboard.Clipboard) directly, which
    KDE's Wayland compositor silently drops for a background daemon like
    AutoKey (no input-event serial to offer for
    wl_data_device.set_selection()). The call returns without error and
    QClipboard reads its own value back afterward, but no other client
    (xclip, or the application the paste is meant to land in) ever sees
    the change. On KDE Wayland specifically, fill_clipboard() must instead
    call klipper's setClipboardContents D-Bus method, since klipper is not
    an ordinary Wayland client and does not hit that rejection.
    """
    original_session_type = autokey.common.SESSION_TYPE
    original_desktop = autokey.common.DESKTOP
    try:
        autokey.common.SESSION_TYPE = "wayland"
        autokey.common.DESKTOP = "KDE"
        clipboard = api.clipboard_qt.QtClipboard.__new__(api.clipboard_qt.QtClipboard)
        clipboard._klipper_interface = unittest.mock.Mock()
        clipboard.fill_clipboard("test contents")
        clipboard._klipper_interface.setClipboardContents.assert_called_once_with("test contents")
    finally:
        autokey.common.SESSION_TYPE = original_session_type
        autokey.common.DESKTOP = original_desktop


def test_qt_clipboard_read_routes_through_klipper_on_kde_wayland():
    """
    Regression test for the read-side half of the same bug:
    QClipboard.text(QClipboard.Clipboard) has the same underlying problem
    as the write side, just less visible -- it returns without error but
    can read back stale/empty content instead of what another client
    actually currently holds (confirmed live: reading immediately after an
    external xclip set returned '' via QClipboard while klipper's own
    getClipboardContents() correctly returned the just-set value). Without
    this, AutoKey's own clipboard-restore-after-paste backup step captures
    the wrong (empty) value to restore.
    """
    original_session_type = autokey.common.SESSION_TYPE
    original_desktop = autokey.common.DESKTOP
    try:
        autokey.common.SESSION_TYPE = "wayland"
        autokey.common.DESKTOP = "KDE"
        clipboard = api.clipboard_qt.QtClipboard.__new__(api.clipboard_qt.QtClipboard)
        clipboard._klipper_interface = unittest.mock.Mock()
        clipboard._klipper_interface.getClipboardContents.return_value = "klipper contents"
        hm.assert_that(clipboard.get_clipboard(), hm.equal_to("klipper contents"))
    finally:
        autokey.common.SESSION_TYPE = original_session_type
        autokey.common.DESKTOP = original_desktop


def test_qt_clipboard_falls_back_when_klipper_unavailable_on_write():
    """
    Regression test for a real crash risk flagged in review: klipper is
    KDE's *default* clipboard manager, not the only one -- a user can
    disable it or run an alternative (e.g. CopyQ) instead. Connecting to a
    D-Bus service that isn't running raises (pydbus/GLib raise
    org.freedesktop.DBus.Error.ServiceUnknown), and prior to this fix that
    exception was unhandled, so every clipboard-paste on KDE Wayland would
    crash outright for any user without klipper running -- worse than the
    original silent-non-sync bug #1250 fixed. fill_clipboard() must fall
    back to Qt's own clipboard API (the pre-#1250 behavior) instead of
    raising.
    """
    original_session_type = autokey.common.SESSION_TYPE
    original_desktop = autokey.common.DESKTOP
    try:
        autokey.common.SESSION_TYPE = "wayland"
        autokey.common.DESKTOP = "KDE"
        clipboard = api.clipboard_qt.QtClipboard.__new__(api.clipboard_qt.QtClipboard)
        clipboard.app = None
        clipboard._klipper_interface = None
        with patch("pydbus.SessionBus") as mock_bus:
            mock_bus.return_value.get.side_effect = Exception("ServiceUnknown")
            clipboard.fill_clipboard("test contents")
            hm.assert_that(clipboard.clipBoard.text(QClipboard.Clipboard), hm.equal_to("test contents"))
    finally:
        autokey.common.SESSION_TYPE = original_session_type
        autokey.common.DESKTOP = original_desktop


def test_qt_clipboard_falls_back_when_klipper_unavailable_on_read():
    """Read-side counterpart of test_qt_clipboard_falls_back_when_klipper_unavailable_on_write."""
    original_session_type = autokey.common.SESSION_TYPE
    original_desktop = autokey.common.DESKTOP
    try:
        autokey.common.SESSION_TYPE = "wayland"
        autokey.common.DESKTOP = "KDE"
        clipboard = api.clipboard_qt.QtClipboard.__new__(api.clipboard_qt.QtClipboard)
        clipboard.app = None
        clipboard.text = None
        clipboard._klipper_interface = None
        clipboard.clipBoard.setText("already on qt clipboard", QClipboard.Clipboard)
        with patch("pydbus.SessionBus") as mock_bus:
            mock_bus.return_value.get.side_effect = Exception("ServiceUnknown")
            hm.assert_that(clipboard.get_clipboard(), hm.equal_to("already on qt clipboard"))
    finally:
        autokey.common.SESSION_TYPE = original_session_type
        autokey.common.DESKTOP = original_desktop


def test_get_klipper_interface_caches_unavailability_and_does_not_retry():
    """
    A missing klipper service shouldn't be re-probed on every single
    clipboard operation -- _get_klipper_interface() caches the failure
    (via a False sentinel, distinct from the None-means-not-yet-tried
    initial state) after the first attempt.
    """
    clipboard = api.clipboard_qt.QtClipboard.__new__(api.clipboard_qt.QtClipboard)
    clipboard._klipper_interface = None
    with patch("pydbus.SessionBus") as mock_bus:
        mock_bus.return_value.get.side_effect = Exception("ServiceUnknown")
        hm.assert_that(clipboard._get_klipper_interface(), hm.equal_to(None))
        hm.assert_that(clipboard._get_klipper_interface(), hm.equal_to(None))
        hm.assert_that(mock_bus.return_value.get.call_count, hm.equal_to(1))


def test_qt_clipboard_does_not_use_klipper_on_gnome_or_x11():
    """
    This is a KDE Wayland-specific rejection; GNOME and X11 must not route
    through klipper (which is a KDE-specific service that may not even be
    running there).
    """
    original_session_type = autokey.common.SESSION_TYPE
    original_desktop = autokey.common.DESKTOP
    try:
        for session_type, desktop in [("wayland", "GNOME"), ("x11", "KDE"), (None, "")]:
            autokey.common.SESSION_TYPE = session_type
            autokey.common.DESKTOP = desktop
            clipboard = api.clipboard_qt.QtClipboard.__new__(api.clipboard_qt.QtClipboard)
            hm.assert_that(
                clipboard._use_klipper_for_clipboard(),
                hm.equal_to(False),
                "Should not use klipper for session_type={!r}, desktop={!r}".format(
                    session_type, desktop)
            )
    finally:
        autokey.common.SESSION_TYPE = original_session_type
        autokey.common.DESKTOP = original_desktop
