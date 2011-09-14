#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Chris Dekter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import threading, logging, os.path, time

from pyinotify import WatchManager, Notifier, EventsCodes, ProcessEvent

_logger = logging.getLogger("inotify")

m = EventsCodes.OP_FLAGS
MASK = m["IN_CREATE"]|m["IN_MODIFY"]|m["IN_DELETE"]|m["IN_MOVED_TO"]|m["IN_MOVED_FROM"]

class Processor(ProcessEvent):
    
    def __init__(self, monitor, listener):
        ProcessEvent.__init__(self)
        self.listener = listener
        self.monitor = monitor
        
    def __getEventPath(self, event):
        if event.name != '':
            path = os.path.join(event.path, event.name)
        else:
            path = event.path
        _logger.info("Reporting %s event at %s", event.maskname, path)
        return path
    
    def process_IN_MOVED_TO(self, event):
        path = self.__getEventPath(event)
        if not self.monitor.is_suspended(path):
            self.listener.path_created_or_modified(path)
    
    def process_IN_CREATE(self, event):
        path = self.__getEventPath(event)
        if not self.monitor.is_suspended(path):
            self.listener.path_created_or_modified(path)
        
    def process_IN_MODIFY(self, event):
        path = self.__getEventPath(event)
        if not self.monitor.is_suspended(path):
            self.listener.path_created_or_modified(path)
        
    def process_IN_DELETE(self, event):
        path = self.__getEventPath(event)
        if not self.monitor.is_suspended(path):        
            self.listener.path_removed(path)


class FileMonitor(threading.Thread):
    
    def __init__(self, listener):
        threading.Thread.__init__(self)
        self.__p = Processor(self, listener)
        self.manager = WatchManager()
        self.notifier = Notifier(self.manager, self.__p)
        self.event = threading.Event()
        self.setDaemon(True)
        self.watches = []
        self.suspended = []
            
    def suspend_path(self, path):
        self.suspended.append(path)
        
    def unsuspend_path(self, path):
        t = threading.Thread(target=self.__unsuspend, args=(path,))
        t.start()
        
    def __unsuspend(self, path):
        time.sleep(1)
        self.suspended.remove(path)
        
    def is_suspended(self, path):
        return path in self.suspended
        
    def has_watch(self, path):
        return path in self.watches
    
    def add_watch(self, path):
        _logger.debug("Adding watch for %s", path)
        self.manager.add_watch(path, MASK, self.__p)
        self.watches.append(path)
        
    def remove_watch(self, path):
        _logger.debug("Removing watch for %s", path)
        wd = self.manager.get_wd(path)
        self.manager.rm_watch(wd, True)
        self.watches.remove(path)
        for i in range(len(self.watches)):
            try:
                if self.watches[i].startswith(path):
                    self.watches.remove(self.watches[i])
            except IndexError:
                break
    
        if path in self.suspended: self.suspended.remove(path)
        for i in range(len(self.suspended)):
            try:
                if self.suspended[i].startswith(path):
                    self.suspended.remove(self.suspended[i])
            except IndexError:
                break        
        
    def run(self):        
        while not self.event.isSet():
            self.notifier.process_events()
            if self.notifier.check_events():
                self.notifier.read_events()
        
        _logger.info("Shutting down file monitor")
        for path in self.watches:
            wd = self.manager.get_wd(path)
            self.manager.rm_watch(wd, True)
        
    def stop(self):
        self.event.set()
        
        
"""class MonitoredPath:
    
    def __init__(self, path, monitor, isDir):
        self.suspended = False
        self.path = path
        self.monitor = monitor
        self.isDir = isDir        
        
    def callback(self, path, eType):
        _logger.debug("Got modification event under path %s:\n\t%s, %d", self.path, path, eType)
        if not eType in (2, 5):
            return
    
        if self.suspended:
            return
    
        if self.isDir and not path.startswith(self.path):
            self.monitor.handle_event(self.path + '/' + path, eType)
        else:
            self.monitor.handle_event(self.path, eType)
        

class WatchMonitorWrapper(gamin.WatchMonitor):
    
    def fileno(self):
        return self.get_fd()"""
    
