import logging
from typing import Dict, Optional

import evdev

logger = logging.getLogger(__name__)

# Digitizer/stylus button codes that should not be included in the merged
# device capabilities. Their presence alongside ABS axes causes libinput to
# classify the device as a graphics tablet; combined with a zero ABS
# resolution (common for tablet/digitizer devices), libinput drops the
# device entirely on Wayland.
TABLET_STYLUS_BUTTON_CODES = set(range(320, 338))


def _merge_capabilities(device_paths):
    """Merge input device capabilities for creating a synthetic uinput device.

    Applies the following sanitization to avoid libinput silently dropping
    the device on Wayland (libinput-based compositors):

    1. Replace any ABS axis with ``resolution == 0`` with ``resolution == 1``.
       AutoKey does no genuine absolute-positioning calibration, so any small
       positive value is sufficient.
    2. Drop digitizer/stylus ``EV_KEY`` codes (evdev codes 320-337) from the
       merged capability set. Without these codes the merged device is not
       classified as a tablet by libinput's heuristic.
    """
    events: Dict[int, dict] = {}
    for path in device_paths:
        device = evdev.Device(path)
        for evtype, typeinfo in device.capabilities().items():
            for absinfo_or_code, spec in typeinfo.items():
                key = (evtype, absinfo_or_code)

                # Sanitize zero-resolution ABS axes.
                if evtype == evdev.EV_ABS and hasattr(spec, "resolution"):
                    if spec.resolution == 0:
                        from evdev import AbsInfo
                        spec = AbsInfo(
                            value=spec.value,
                            min=spec.min,
                            max=spec.max,
                            fuzz=spec.fuzz,
                            flat=spec.flat,
                            resolution=1,
                        )

                # Drop digitizer/stylus button codes (evdev 320-337).
                if evtype == evdev.EV_KEY and absinfo_or_code in TABLET_STYLUS_BUTTON_CODES:
                    continue

                events[key] = spec
        device.close()
    return events


class UInputInterface:
    def __init__(self, device_paths, name="autokey mouse and keyboard"):
        self.device_paths = device_paths
        self.name = name
        self.ui = None

    def initialize(self):
        if self.ui is not None:
            return

        events = _merge_capabilities(self.device_paths)
        self.ui = evdev.UInput(events=events, name=self.name)
        logger.debug(
            "Created uinput device %r with %d capability entries",
            self.ui.path,
            len(events),
        )

    def send_event(self, event):
        if self.ui is None:
            return
        self.ui.write(event.type, event.code, event.value)

    def close(self):
        if self.ui is not None:
            self.ui.close()
            self.ui = None
