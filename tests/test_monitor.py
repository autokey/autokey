# Copyright (C) 2026 Aryan Mangal
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

"""Tests for the bookkeeping and error handling of autokey.monitor.FileMonitor.

The inotify machinery itself is replaced by mocks, so these tests do not touch
the file system watches of the machine they run on.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from autokey import monitor as monitor_module
from autokey.monitor import FileMonitor


@pytest.fixture
def file_monitor():
    with patch.object(monitor_module, "WatchManager"), patch.object(monitor_module, "Notifier"):
        yield FileMonitor(MagicMock())


def test_run_keeps_monitoring_after_an_exception(file_monitor):
    """An exception while processing events must not end the monitor thread."""
    calls = []

    def process_events():
        calls.append(1)
        if len(calls) == 1:
            raise AttributeError("raised by a listener callback")
        file_monitor.event.set()  # Second pass succeeds, ask the loop to finish.

    file_monitor.notifier.process_events.side_effect = process_events
    file_monitor.notifier.check_events.return_value = False
    file_monitor.event.wait = MagicMock()  # Do not really sleep in the back-off.

    file_monitor.run()

    assert len(calls) == 2
    file_monitor.event.wait.assert_called_once()
    file_monitor.notifier.stop.assert_called_once()


def test_unsuspend_removes_every_stale_watch(file_monitor, tmp_path):
    """Consecutive stale watches must all be dropped, existing ones kept."""
    existing = tmp_path / "existing"
    existing.mkdir()
    stale = [str(tmp_path / name) for name in ("gone1", "gone2", "gone3", "gone4")]
    file_monitor.watches = [stale[0], stale[1], str(existing), stale[2], stale[3]]

    with patch.object(monitor_module.time, "sleep"):
        file_monitor._FileMonitor__unsuspend()  # pylint: disable=protected-access

    assert file_monitor.watches == [str(existing)]
    assert not file_monitor.is_suspended()


def test_remove_watch_forgets_all_children(file_monitor):
    root = os.path.join(os.sep, "data", "Foo")
    file_monitor.watches = [root, os.path.join(root, "a"), os.path.join(root, "b"), os.path.join(root, "c", "d")]
    file_monitor.manager.get_wd.return_value = 7

    file_monitor.remove_watch(root)

    file_monitor.manager.rm_watch.assert_called_once_with(7, True)
    assert file_monitor.watches == []


def test_remove_watch_keeps_sibling_with_same_prefix(file_monitor):
    """Removing ".../Foo" must not forget the unrelated watch on ".../Foobar"."""
    base = os.path.join(os.sep, "data")
    foo, foobar = os.path.join(base, "Foo"), os.path.join(base, "Foobar")
    file_monitor.watches = [foo, foobar, os.path.join(foo, "sub")]
    file_monitor.manager.get_wd.return_value = 7

    file_monitor.remove_watch(foo)

    assert file_monitor.watches == [foobar]
    assert file_monitor.has_watch(foobar)
    assert not file_monitor.has_watch(foo)


def test_remove_watch_of_unwatched_path_does_not_raise(file_monitor):
    file_monitor.watches = [os.path.join(os.sep, "data", "other")]
    file_monitor.manager.get_wd.return_value = None

    file_monitor.remove_watch(os.path.join(os.sep, "data", "unknown"))

    file_monitor.manager.rm_watch.assert_not_called()
    assert file_monitor.watches == [os.path.join(os.sep, "data", "other")]
