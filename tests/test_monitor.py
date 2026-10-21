import threading

import pytest

from autokey.monitor import FileMonitor


class Listener:
    def __init__(self):
        self.paths = []
        self.seen = threading.Event()
        self.fail_first = True

    def path_created_or_modified(self, path):
        self.paths.append(path)
        if self.fail_first:
            self.fail_first = False
            raise AttributeError("raised by the listener")
        self.seen.set()

    def path_removed(self, path):
        pass


@pytest.fixture
def monitor(tmp_path):
    listener = Listener()
    file_monitor = FileMonitor(listener)
    file_monitor.add_watch(str(tmp_path))
    file_monitor.start()
    yield file_monitor, listener
    file_monitor.stop()
    file_monitor.join(5)


def test_monitor_thread_survives_a_listener_exception(monitor, tmp_path):
    """
    An exception raised by the listener (for instance Qt's Application.path_created_or_modified() running before
    its configWindow existed) used to end the monitor thread, so no later config file change was ever noticed.
    """
    file_monitor, listener = monitor

    (tmp_path / "first").write_text("a")
    (tmp_path / "second").write_text("b")

    assert listener.seen.wait(5)
    assert file_monitor.is_alive()
    assert len(listener.paths) >= 2


def test_qt_application_has_a_config_window_placeholder_before_initialise():
    """The monitor thread calls path_created_or_modified() with self.configWindow during first-run setup."""
    qtapp = pytest.importorskip("autokey.qtapp")

    assert qtapp.Application.configWindow is None
