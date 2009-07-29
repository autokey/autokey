# -*- coding: utf-8 -*-

# Copyright (C) 2009 Chris Dekter

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from PyKDE4.kdeui import KNotification, KSystemTrayIcon, KIcon, KStandardAction, KToggleAction
from PyKDE4.kdecore import i18n
from PyQt4.QtCore import SIGNAL

import popupmenu
from .. configmanager import *

ICON_FILE = "/usr/share/pixmaps/akicon.png"

TOOLTIP_RUNNING = "AutoKey - running"
TOOLTIP_PAUSED = "AutoKey - paused"

class Notifier:
    
    def __init__(self, app):
        self.app = app
        self.configManager = app.configManager
        
        if ConfigManager.SETTINGS[SHOW_TRAY_ICON]:
            self.icon = KSystemTrayIcon(ICON_FILE)
            self.build_menu()
            self.update_tool_tip()
            self.icon.show()
                        
    def update_tool_tip(self):
        if ConfigManager.SETTINGS[SERVICE_RUNNING]:
            self.icon.setToolTip(TOOLTIP_RUNNING)
            self.toggleAction.setChecked(True)
        else:
            self.icon.setToolTip(TOOLTIP_PAUSED)
            self.toggleAction.setChecked(False)
            
    def build_menu(self):
        if ConfigManager.SETTINGS[SHOW_TRAY_ICON]:
            # Get phrase folders to add to main menu
            folders = []
            items = []

            for folder in self.configManager.allFolders:
                if folder.showInTrayMenu:
                    folders.append(folder)
            
            for item in self.configManager.allItems:
                if item.showInTrayMenu:
                    items.append(item)
                    
            # Construct main menu
            menu = popupmenu.PopupMenu(self.app.service, folders, items, False, "AutoKey")
            if len(items) > 0:
                menu.addSeparator()
            
            self.toggleAction = KToggleAction(i18n("&Enable Monitoring"), menu)
            self.toggleAction.connect(self.toggleAction, SIGNAL("triggered()"), self.on_enable_toggled)
            self.toggleAction.setChecked(self.app.service.is_running())
            self.toggleAction.setEnabled(not self.app.serviceDisabled)           
            
            menu.addAction(self.toggleAction)
            menu.addAction(KIcon("edit-clear"), i18n("&Hide Icon"), self.on_hide_icon)
            menu.addAction(KIcon("configure"), i18n("&Configure..."), self.on_configure)
            menu.addAction(KStandardAction.quit(self.on_quit, menu))
            self.icon.setContextMenu(menu)

    # ---- Signal handlers ----

    def on_quit(self):
        self.app.shutdown()

    def on_configure(self):
        self.app.show_configure()
        
    def on_enable_toggled(self):
        if self.toggleAction.isChecked():
            self.app.unpause_service()
        else:
            self.app.pause_service()
            
    def on_hide_icon(self):
        self.icon.hide()
        ConfigManager.SETTINGS[SHOW_TRAY_ICON] = False