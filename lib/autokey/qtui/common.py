# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>

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

import re
import os.path
import pathlib
import enum
import functools

from PyQt5.QtCore import QFile, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import QMessageBox, QLabel
from PyQt5 import uic
from PyQt5.QtSvg import QSvgRenderer

import autokey.configmanager.configmanager_constants as cm_constants
from autokey.logger import get_logger

try:
    import autokey.qtui.compiled_resources
except ModuleNotFoundError:
    import warnings
    # No compiled resource module found. Load bare files from disk instead.
    warn_msg = "Compiled Qt resources file not found. If autokey is launched directly from the source directory, " \
               "this is expected and harmless. If not, this indicates a failure in the resource compilation."
    warnings.warn(warn_msg)
    RESOURCE_PATH_PREFIX = str(pathlib.Path(__file__).resolve().parent / "resources")
    local_path = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "config"
    if local_path.exists():
        # This is running from the source directory, thus icons are in <root>/config
        ICON_PATH_PREFIX = str(local_path)
    else:
        # This is an installation. Icons reside in autokey/qtui/resources/icons, where they were copied by setup.py
        ICON_PATH_PREFIX = str(pathlib.Path(__file__).resolve().parent / "resources" / "icons")
    del local_path
else:
    import atexit
    # Compiled resources found, so use it.
    RESOURCE_PATH_PREFIX = ":"
    ICON_PATH_PREFIX = ":/icons"
    atexit.register(autokey.qtui.compiled_resources.qCleanupResources)

logger = get_logger(__name__)
del get_logger
EMPTY_FIELD_REGEX = re.compile(r"^ *$", re.UNICODE)


def monospace_font() -> QFont:
    """
    Returns a monospace font used in the code editor widgets.
    :return: QFont instance having a monospace font.
    """
    font = QFont("monospace")
    font.setStyleHint(QFont.Monospace)
    return font


def set_url_label(label: QLabel, path: str):

    # In both cases, only replace the first occurence.
    if path.startswith(cm_constants.CONFIG_DEFAULT_FOLDER):
        text = path.replace(cm_constants.CONFIG_DEFAULT_FOLDER, "(Default folder)", 1)
    else:
        # if bob has added a path '/home/bob/some/folder/home/bobbie/foo/' to autokey, the desired replacement text
        # is '~/some/folder/home/bobbie/foo/' and NOT '~/some/folder~bie/foo/'
        text = path.replace(os.path.expanduser("~"), "~", 1)
    url = "file://" + path
    if not label.openExternalLinks():
        # The openExternalLinks property is not set in the UI file, so fail fast instead of doing workarounds.
        raise ValueError("QLabel with disabled openExternalLinks property used to display an external URL. "
                         "This won’t work, so fail now. Label: {}, Text: {}".format(label, label.text()))
    # TODO elide text?
    label.setText("""<a href="{url}">{text}</a>""".format(url=url, text=text))


def validate(expression, message, widget, parent):
    if not expression:
        QMessageBox.critical(parent, message, message)
        if widget is not None:
            widget.setFocus()
    return expression


class AutoKeyIcon(enum.Enum):
    AUTOKEY = "autokey.png"
    AUTOKEY_SCALABLE = "autokey.svg"
    SYSTEM_TRAY = "autokey-status.svg"
    SYSTEM_TRAY_DARK = "autokey-status-dark.svg"
    SYSTEM_TRAY_ERROR = "autokey-status-error.svg"


@functools.lru_cache()
def load_icon(name: AutoKeyIcon) -> QIcon:
    file_path = ICON_PATH_PREFIX + "/" + name.value
    icon = QIcon(file_path)
    if not icon.availableSizes() and file_path.endswith(".svg"):
        # FIXME: Work around Qt Bug: https://bugreports.qt.io/browse/QTBUG-63187
        # Manually render the SVG to some common icon sizes.
        icon = QIcon()  # Discard the bugged QIcon
        renderer = QSvgRenderer(file_path)
        for size in (16, 22, 24, 32, 64, 128):
            pixmap = QPixmap(QSize(size, size))
            pixmap.fill(QColor(255, 255, 255, 0))
            renderer.render(QPainter(pixmap))
            icon.addPixmap(pixmap)
    return icon


def _get_ui_qfile(name: str):
    """
    Returns an opened, read-only QFile for the given QtDesigner UI file name. Expects a plain name like "centralwidget".
    The file ending and resource path is added automatically.
    Raises FileNotFoundError, if the given ui file does not exist.
    :param name:
    :return:
    """
    file_path = RESOURCE_PATH_PREFIX + "/ui/{ui_file_name}.ui".format(ui_file_name=name)
    file = QFile(file_path)
    if not file.exists():
        raise FileNotFoundError("UI file not found: " + file_path)
    file.open(QFile.ReadOnly)
    return file


def load_ui_from_file(name: str):
    """
    Returns a tuple from uic.loadUiType(), loading the ui file with the given name.
    :param name:
    :return:
    """
    ui_file = _get_ui_qfile(name)
    try:
        base_type = uic.loadUiType(ui_file, from_imports=True)
    finally:
        ui_file.close()
    return base_type


"""
This renamed function is supposed to be used during class definition to make the intention clear.
Usage example:

class SomeWidget(*inherits_from_ui_file_with_name("SomeWidgetUiFileName")):
    def __init__(self, parent):
        super(SomeWidget, self).__init__(parent)
        self.setupUi(self)


"""
inherits_from_ui_file_with_name = load_ui_from_file
