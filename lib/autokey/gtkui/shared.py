import os
from gi.repository import Gtk

from autokey.i18n import DOMAIN


def get_ui(fileName):
    builder = Gtk.Builder()
    builder.set_translation_domain(DOMAIN)
    uiFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/" + fileName)
    builder.add_from_file(uiFile)
    return builder
