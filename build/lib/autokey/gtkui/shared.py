import os
from gi.repository import Gtk


def get_ui(fileName):
    builder = Gtk.Builder()
    uiFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/" + fileName)
    builder.add_from_file(uiFile)
    return builder
