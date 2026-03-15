# Game Controller Support for AutoKey

This document describes the game controller input support added to AutoKey.

## Overview

AutoKey now supports using game controllers (gamepads, joysticks) as input triggers
for phrases and scripts. This allows you to:

- Use an old game controller as a macro pad
- Trigger actions with gamepad buttons
- Use analog stick movements as triggers

## Requirements

To use game controller support, install the `evdev` Python library:

```bash
pip install evdev
```

On Debian/Ubuntu systems:
```bash
sudo apt-get install python3-evdev
```

## Usage

### Python API

```python
from autokey.model import Phrase, Script
from autokey.model.abstract_controller import ControllerButton, ControllerAxis

# Create a phrase triggered by controller button
phrase = Phrase("Hello", "Hello World!")
phrase.set_controller_trigger(button=ControllerButton.A)

# Create a script triggered by axis movement
script = Script("Volume Up", "system.set_volume_up()")
script.set_controller_trigger(axis=ControllerAxis.RT, threshold=20000)
```

### Supported Buttons

- `A`, `B`, `X`, `Y` - Face buttons
- `START`, `SELECT`, `HOME` - System buttons
- `LB`, `RB` - Left/Right bumpers
- `LS`, `RS` - Left/Right stick press
- `DPAD_UP`, `DPAD_DOWN`, `DPAD_LEFT`, `DPAD_RIGHT` - D-Pad directions

### Supported Axes

- `LS_X`, `LS_Y` - Left stick X/Y
- `RS_X`, `RS_Y` - Right stick X/Y
- `LT`, `RT` - Left/Right triggers

## Configuration

Controller triggers can be configured programmatically or through the JSON
configuration files. Example configuration:

```json
{
    "type": "phrase",
    "description": "Quick Action",
    "modes": [4],
    "controller": {
        "controller_button": "A",
        "controller_axis": null,
        "axis_threshold": 16384,
        "controller_name_filter": ""
    },
    ...
}
```

## Permissions

On Linux, accessing input devices may require root privileges or membership in
the `input` group:

```bash
sudo usermod -a -G input $USER
```

You may also need to create a udev rule for your controller:

```bash
# /etc/udev/rules.d/99-gamepad.rules
SUBSYSTEM=="input", ATTRS{name}=="*Controller*", MODE="0666"
```

Then reload udev rules:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Technical Details

The controller support uses the Linux `evdev` interface for direct hardware
access. It supports:

- Auto-detection of connected controllers
- Multiple simultaneous controllers
- Window filtering (trigger only in specific windows)
- Button press/release detection
- Analog axis threshold triggers

## Troubleshooting

### Controllers not detected

1. Check that evdev is installed: `python3 -c "import evdev; print('OK')"`
2. Verify controller is detected by the system: `ls /dev/input/event*`
3. Check that your user has permission to access input devices

### Events not triggering

1. Check AutoKey logs for controller events
2. Verify the controller name filter if set
3. Check window filtering settings

## Implementation Notes

The controller support is implemented in:
- `lib/autokey/controller.py` - Core controller handling
- `lib/autokey/model/abstract_controller.py` - Model mixin for controller triggers
- `lib/autokey/service.py` - Integration with service event loop
