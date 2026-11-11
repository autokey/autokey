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

import threading
import os.path
import time

from pyinotify import WatchManager, Notifier, EventsCodes, ProcessEvent


logger = __import__("autokey.logger").logger.get_logger(__name__)
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
        logger.debug("Reporting %s event at %s", event.maskname, path)
        return path

    def process_IN_MOVED_TO(self, event):
        path = self.__getEventPath(event)
        if not self.monitor.is_suspended():
            self.listener.path_created_or_modified(path)

    def process_IN_CREATE(self, event):
        path = self.__getEventPath(event)
        if not self.monitor.is_suspended():
            self.listener.path_created_or_modified(path)

    def process_IN_MODIFY(self, event):
        path = self.__getEventPath(event)
        if not self.monitor.is_suspended():
            self.listener.path_created_or_modified(path)

    def process_IN_DELETE(self, event):
        path = self.__getEventPath(event)
        if not self.monitor.is_suspended():
            self.listener.path_removed(path)

    def process_IN_MOVED_FROM(self, event):
        path = self.__getEventPath(event)
        if not self.monitor.is_suspended():
            self.listener.path_removed(path)


class FileMonitor(threading.Thread):

    def __init__(self, listener):
        threading.Thread.__init__(self)
        self.__p = Processor(self, listener)
        self.manager = WatchManager()
        self.notifier = Notifier(self.manager, self.__p)
        self.event = threading.Event()
        self.daemon = True
        self.watches = []
        self.__isSuspended = False

    def suspend(self):
        self.__isSuspended = True

    def unsuspend(self):
        t = threading.Thread(target=self.__unsuspend)
        t.start()

    def __unsuspend(self):
        time.sleep(1.5)
        self.__isSuspended = False
        # Iterate over a copy: removing from the list being iterated skips the
        # entry following each removed one, leaving some stale watches behind.
        for watch in list(self.watches):
            if not os.path.exists(watch):
                logger.debug("Removed stale watch on %s", watch)
                self.watches.remove(watch)

    def is_suspended(self):
        return self.__isSuspended

    def has_watch(self, path):
        return path in self.watches

    def add_watch(self, path):
        logger.debug("Adding watch for %s", path)
        self.manager.add_watch(path, MASK, self.__p)
        self.watches.append(path)

    def remove_watch(self, path):
        logger.debug("Removing watch for %s", path)
        wd = self.manager.get_wd(path)
        if wd is not None:
            self.manager.rm_watch(wd, True)
        # Forget `path` and everything below it. Compare against "path/" so that a
        # sibling sharing the same name prefix ("Foo" vs "Foobar") is kept, and
        # rebuild the list instead of removing from it while indexing it.
        prefix = os.path.join(path, "")
        self.watches[:] = [w for w in self.watches if w != path and not w.startswith(prefix)]

    def run(self):
        while not self.event.is_set():
            try:
                self.notifier.process_events()
                if self.notifier.check_events(1000):
                    self.notifier.read_events()
            except Exception:  # pylint: disable=broad-except
                # An exception raised by a listener callback must not end this
                # thread: it would silently stop all file monitoring until restart.
                logger.exception("Error while processing file system events, continuing to monitor")
                self.event.wait(1)

        logger.info("Shutting down file monitor")
        self.notifier.stop()

    def stop(self):
        self.event.set()
        self.join()
