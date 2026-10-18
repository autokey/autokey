# Regression tests for issue #1001: checkOptionalPrograms() warned about
# missing visgrep/import/png2pat (xautomation/ImageMagick, backing the
# `highlevel` scripting API) unconditionally, even under Wayland where that
# API is entirely disabled (see highlevel_disabled.py) and those tools can
# never be useful. x11_optional_programs (xte/xmousepos) was already
# correctly gated behind an X11 session; optional_programs was not.
import unittest.mock

import autokey.UI_common_functions as ui_common


def test_x11_only_programs_are_not_checked_under_wayland(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    with unittest.mock.patch.object(ui_common, "checkProgramImports") as check:
        ui_common.checkOptionalPrograms()
    check.assert_not_called()


def test_x11_only_programs_are_checked_under_x11(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    with unittest.mock.patch.object(ui_common, "checkProgramImports") as check:
        ui_common.checkOptionalPrograms()
    checked = [call.args[0] for call in check.call_args_list]
    assert ui_common.x11_optional_programs in checked
    assert ui_common.optional_programs in checked
