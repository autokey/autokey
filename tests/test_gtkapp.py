"""
Regression test for the GTK Application.unpause_service() copy-paste bug:
it called super().pause_service() instead of super().unpause_service(), so
re-enabling AutoKey via the tray icon's "Enable Monitoring" checkbox (or the
org.autokey.Service D-Bus unpause_service method) silently re-paused the
service instead of resuming it. Confirmed live: a fresh AutoKey process's
very first unpause_service() call logged "Pausing", not "Unpausing".
"""
from unittest.mock import MagicMock, patch

import autokey.gtkapp
from autokey.autokey_app import AutokeyApplication


def _make_app():
    app = autokey.gtkapp.Application.__new__(autokey.gtkapp.Application)
    app.notifier = MagicMock()
    return app


def test_unpause_service_calls_base_unpause_not_pause():
    app = _make_app()
    with patch.object(AutokeyApplication, "unpause_service") as base_unpause, \
         patch.object(AutokeyApplication, "pause_service") as base_pause:
        app.unpause_service()
    base_unpause.assert_called_once()
    base_pause.assert_not_called()


def test_pause_service_calls_base_pause_not_unpause():
    app = _make_app()
    with patch.object(AutokeyApplication, "unpause_service") as base_unpause, \
         patch.object(AutokeyApplication, "pause_service") as base_pause:
        app.pause_service()
    base_pause.assert_called_once()
    base_unpause.assert_not_called()


def test_unpause_service_updates_tray_tooltip():
    app = _make_app()
    with patch.object(AutokeyApplication, "unpause_service"):
        app.unpause_service()
    app.notifier.update_tool_tip.assert_called_once()
