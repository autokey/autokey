#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" evdev.py

This is a Python interface to the Linux input system's event device.
Events can be read from an open event file and decoded into spiffy
python objects. The Event objects can optionally be fed into a Device
object that represents the complete state of the device being monitored.

Copyright (C) 2003-2004 Micah Dowty <micah@navi.cx>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import struct, sys, os, time, select
from fcntl import ioctl

__all__ = ["DeviceGroup"]

def demo():
    """Open the event device named on the command line, use incoming
       events to update a device, and show the state of this device.
       """
    dev = DeviceGroup(sys.argv[1:])
    while 1:
        event = dev.next_event()
        if event is not None:
            print repr(event)
            if event.type == "EV_KEY" and event.value == 1:
                if event.code.startswith("KEY"):
                    print event.scanCode
                elif event.code.startswith("BTN"):
                    print event.code

class BaseDevice:
    """Base class representing the state of an input device, with axes and buttons.
       Event instances can be fed into the Device to update its state.
       """
    def __init__(self):
        self.axes = {}
        self.buttons = {}
        self.name = None

    def __repr__(self):
        return "<Device name=%r axes=%r buttons=%r>" % (
            self.name, self.axes, self.buttons)

    def update(self, event):
        f = getattr(self, "update_%s" % event.type, None)
        if f:
            f(event)

    def update_EV_KEY(self, event):
        self.buttons[event.code] = event.value

    def update_EV_ABS(self, event):
        self.axes[event.code] = event.value

    def update_EV_REL(self, event):
        self.axes[event.code] = self.axes.get(event.code, 0) + event.value

    def __getitem__(self, name):
        """Retrieve the current value of an axis or button,
           or zero if no data has been received for it yet.
           """
        if name in self.axes:
            return self.axes[name]
        else:
            return self.buttons.get(name, 0)


# evdev ioctl constants. The horrible mess here
# is to silence silly FutureWarnings
EVIOCGNAME_512 = ~int(~0x82004506L & 0xFFFFFFFFL)
EVIOCGID       = ~int(~0x80084502L & 0xFFFFFFFFL)
EVIOCGBIT_512  = ~int(~0x81fe4520L & 0xFFFFFFFFL)
EVIOCGABS_512  = ~int(~0x80144540L & 0xFFFFFFFFL)


class Device(BaseDevice):
    """An abstract input device attached to a Linux evdev device node"""
    def __init__(self, filename):
        BaseDevice.__init__(self)
        self.fd = os.open(filename, os.O_RDONLY | os.O_NONBLOCK)
        self.packetSize = Event.get_format_size()
        self.readMetadata()        

    def poll(self):
        """Receive and process all available input events"""
        while 1:
            try:
                buffer = os.read(self.fd, self.packetSize)
            except OSError:
                return
            self.update(Event(unpack=buffer))

    def readMetadata(self):
        """Read device identity and capabilities via ioctl()"""
        buffer = "\0"*512

        # Read the name
        self.name = ioctl(self.fd, EVIOCGNAME_512, buffer)
        self.name = self.name[:self.name.find("\0")]

        # Read info on each absolute axis
        absmap = Event.codeMaps['EV_ABS']
        buffer = "\0" * struct.calcsize("iiiii")
        self.absAxisInfo = {}
        for name, number in absmap.nameMap.iteritems():
            values = struct.unpack("iiiii", ioctl(self.fd, EVIOCGABS_512 + number, buffer))
            values = dict(zip(( 'value', 'min', 'max', 'fuzz', 'flat' ),values))
            self.absAxisInfo[name] = values

    def update_EV_ABS(self, event):
        """Scale the absolute axis into the range [-1, 1] using absAxisInfo"""
        try:
            info = self.absAxisInfo[event.code]
        except KeyError:
            return
        range = float(info['max'] - info['min'])
        self.axes[event.code] = (event.value - info['min']) / range * 2.0 - 1.0

class DeviceGroup:
    """
    Capture events from a group of event devices.
    """
    
    def __init__(self, fileNames):
        self.devices = []
        self.fds = []
        self.packetSize = Event.get_format_size()
        
        for fileName in fileNames:
            self.devices.append(Device(fileName))
        for device in self.devices:
            print repr(device)
            self.fds.append(device.fd)        
            
    def next_event(self):
        r, w, x = select.select(self.fds, [], [], 1)
        for fd in self.fds:
            if fd in r:
                buffer = os.read(fd, self.packetSize)
                event = Event(unpack=buffer)
                return event

        return None
        
    def flush(self):
        for device in self.devices:
            device.poll()
            
    def close(self):
        for fd in self.fds:
            try:
                os.close(fd)
            except:
                print "Warning - failed to close on or more device file descriptors"
                pass
            

class EnumDict:
    """A 1:1 mapping from numbers to strings or other objects, for enumerated
       types and other assigned numbers. The mapping can be queried in either
       direction. All values, by default, map to themselves.
       """
    def __init__(self, numberMap):
        self.numberMap = numberMap
        self.nameMap = {}
        for key, value in numberMap.iteritems():
            self.nameMap[value] = key

    def toNumber(self, name):
        return self.nameMap.get(name, name)

    def fromNumber(self, num):
        return self.numberMap.get(num, num)


class Event:
    """Represents one linux input system event. It can
       be encoded and decoded in the 'struct input_event'
       format used by the kernel. Types and codes are automatically
       encoded and decoded with the #define names used in input.h
       """
    ts_format = "@LL"
    format = "=HHl"

    typeMap = EnumDict({
        0x00: "EV_RST",
        0x01: "EV_KEY",
        0x02: "EV_REL",
        0x03: "EV_ABS",
        0x04: "EV_MSC",
        0x11: "EV_LED",
        0x12: "EV_SND",
        0x14: "EV_REP",
        0x15: "EV_FF",
        })

    codeMaps = {

        "EV_KEY": EnumDict({
        0: "KEY_RESERVED",
        1: "KEY_ESC",
        2: "KEY_1",
        3: "KEY_2",
        4: "KEY_3",
        5: "KEY_4",
        6: "KEY_5",
        7: "KEY_6",
        8: "KEY_7",
        9: "KEY_8",
        10: "KEY_9",
        11: "KEY_0",
        12: "KEY_MINUS",
        13: "KEY_EQUAL",
        14: "KEY_BACKSPACE",
        15: "KEY_TAB",
        16: "KEY_Q",
        17: "KEY_W",
        18: "KEY_E",
        19: "KEY_R",
        20: "KEY_T",
        21: "KEY_Y",
        22: "KEY_U",
        23: "KEY_I",
        24: "KEY_O",
        25: "KEY_P",
        26: "KEY_LEFTBRACE",
        27: "KEY_RIGHTBRACE",
        28: "KEY_ENTER",
        29: "KEY_LEFTCTRL",
        30: "KEY_A",
        31: "KEY_S",
        32: "KEY_D",
        33: "KEY_F",
        34: "KEY_G",
        35: "KEY_H",
        36: "KEY_J",
        37: "KEY_K",
        38: "KEY_L",
        39: "KEY_SEMICOLON",
        40: "KEY_APOSTROPHE",
        41: "KEY_GRAVE",
        42: "KEY_LEFTSHIFT",
        43: "KEY_BACKSLASH",
        44: "KEY_Z",
        45: "KEY_X",
        46: "KEY_C",
        47: "KEY_V",
        48: "KEY_B",
        49: "KEY_N",
        50: "KEY_M",
        51: "KEY_COMMA",
        52: "KEY_DOT",
        53: "KEY_SLASH",
        54: "KEY_RIGHTSHIFT",
        55: "KEY_KPASTERISK",
        56: "KEY_LEFTALT",
        57: "KEY_SPACE",
        58: "KEY_CAPSLOCK",
        59: "KEY_F1",
        60: "KEY_F2",
        61: "KEY_F3",
        62: "KEY_F4",
        63: "KEY_F5",
        64: "KEY_F6",
        65: "KEY_F7",
        66: "KEY_F8",
        67: "KEY_F9",
        68: "KEY_F10",
        69: "KEY_NUMLOCK",
        70: "KEY_SCROLLLOCK",
        71: "KEY_KP7",
        72: "KEY_KP8",
        73: "KEY_KP9",
        74: "KEY_KPMINUS",
        75: "KEY_KP4",
        76: "KEY_KP5",
        77: "KEY_KP6",
        78: "KEY_KPPLUS",
        79: "KEY_KP1",
        80: "KEY_KP2",
        81: "KEY_KP3",
        82: "KEY_KP0",
        83: "KEY_KPDOT",
        84: "KEY_103RD",
        85: "KEY_F13",
        86: "KEY_102ND",
        87: "KEY_F11",
        88: "KEY_F12",
        89: "KEY_F14",
        90: "KEY_F15",
        91: "KEY_F16",
        92: "KEY_F17",
        93: "KEY_F18",
        94: "KEY_F19",
        95: "KEY_F20",
        96: "KEY_KPENTER",
        97: "KEY_RIGHTCTRL",
        98: "KEY_KPSLASH",
        99: "KEY_SYSRQ",
        100: "KEY_RIGHTALT",
        101: "KEY_LINEFEED",
        102: "KEY_HOME",
        103: "KEY_UP",
        104: "KEY_PAGEUP",
        105: "KEY_LEFT",
        106: "KEY_RIGHT",
        107: "KEY_END",
        108: "KEY_DOWN",
        109: "KEY_PAGEDOWN",
        110: "KEY_INSERT",
        111: "KEY_DELETE",
        112: "KEY_MACRO",
        113: "KEY_MUTE",
        114: "KEY_VOLUMEDOWN",
        115: "KEY_VOLUMEUP",
        116: "KEY_POWER",
        117: "KEY_KPEQUAL",
        118: "KEY_KPPLUSMINUS",
        119: "KEY_PAUSE",
        120: "KEY_F21",
        121: "KEY_F22",
        122: "KEY_F23",
        123: "KEY_F24",
        124: "KEY_KPCOMMA",
        125: "KEY_LEFTMETA",
        126: "KEY_RIGHTMETA",
        127: "KEY_COMPOSE",
        128: "KEY_STOP",
        129: "KEY_AGAIN",
        130: "KEY_PROPS",
        131: "KEY_UNDO",
        132: "KEY_FRONT",
        133: "KEY_COPY",
        134: "KEY_OPEN",
        135: "KEY_PASTE",
        136: "KEY_FIND",
        137: "KEY_CUT",
        138: "KEY_HELP",
        139: "KEY_MENU",
        140: "KEY_CALC",
        141: "KEY_SETUP",
        142: "KEY_SLEEP",
        143: "KEY_WAKEUP",
        144: "KEY_FILE",
        145: "KEY_SENDFILE",
        146: "KEY_DELETEFILE",
        147: "KEY_XFER",
        148: "KEY_PROG1",
        149: "KEY_PROG2",
        150: "KEY_WWW",
        151: "KEY_MSDOS",
        152: "KEY_COFFEE",
        153: "KEY_DIRECTION",
        154: "KEY_CYCLEWINDOWS",
        155: "KEY_MAIL",
        156: "KEY_BOOKMARKS",
        157: "KEY_COMPUTER",
        158: "KEY_BACK",
        159: "KEY_FORWARD",
        160: "KEY_CLOSECD",
        161: "KEY_EJECTCD",
        162: "KEY_EJECTCLOSECD",
        163: "KEY_NEXTSONG",
        164: "KEY_PLAYPAUSE",
        165: "KEY_PREVIOUSSONG",
        166: "KEY_STOPCD",
        167: "KEY_RECORD",
        168: "KEY_REWIND",
        169: "KEY_PHONE",
        170: "KEY_ISO",
        171: "KEY_CONFIG",
        172: "KEY_HOMEPAGE",
        173: "KEY_REFRESH",
        174: "KEY_EXIT",
        175: "KEY_MOVE",
        176: "KEY_EDIT",
        177: "KEY_SCROLLUP",
        178: "KEY_SCROLLDOWN",
        179: "KEY_KPLEFTPAREN",
        180: "KEY_KPRIGHTPAREN",
        181: "KEY_INTL1",
        182: "KEY_INTL2",
        183: "KEY_INTL3",
        184: "KEY_INTL4",
        185: "KEY_INTL5",
        186: "KEY_INTL6",
        187: "KEY_INTL7",
        188: "KEY_INTL8",
        189: "KEY_INTL9",
        190: "KEY_LANG1",
        191: "KEY_LANG2",
        192: "KEY_LANG3",
        193: "KEY_LANG4",
        194: "KEY_LANG5",
        195: "KEY_LANG6",
        196: "KEY_LANG7",
        197: "KEY_LANG8",
        198: "KEY_LANG9",
        200: "KEY_PLAYCD",
        201: "KEY_PAUSECD",
        202: "KEY_PROG3",
        203: "KEY_PROG4",
        205: "KEY_SUSPEND",
        206: "KEY_CLOSE",
        220: "KEY_UNKNOWN",
        224: "KEY_BRIGHTNESSDOWN",
        225: "KEY_BRIGHTNESSUP",
        0x100: "BTN_0",
        0x101: "BTN_1",
        0x102: "BTN_2",
        0x103: "BTN_3",
        0x104: "BTN_4",
        0x105: "BTN_5",
        0x106: "BTN_6",
        0x107: "BTN_7",
        0x108: "BTN_8",
        0x109: "BTN_9",
        0x110: "BTN_LEFT",
        0x111: "BTN_RIGHT",
        0x112: "BTN_MIDDLE",
        0x113: "BTN_SIDE",
        0x114: "BTN_EXTRA",
        0x115: "BTN_FORWARD",
        0x116: "BTN_BACK",
        0x120: "BTN_TRIGGER",
        0x121: "BTN_THUMB",
        0x122: "BTN_THUMB2",
        0x123: "BTN_TOP",
        0x124: "BTN_TOP2",
        0x125: "BTN_PINKIE",
        0x126: "BTN_BASE",
        0x127: "BTN_BASE2",
        0x128: "BTN_BASE3",
        0x129: "BTN_BASE4",
        0x12a: "BTN_BASE5",
        0x12b: "BTN_BASE6",
        0x12f: "BTN_DEAD",
        0x130: "BTN_A",
        0x131: "BTN_B",
        0x132: "BTN_C",
        0x133: "BTN_X",
        0x134: "BTN_Y",
        0x135: "BTN_Z",
        0x136: "BTN_TL",
        0x137: "BTN_TR",
        0x138: "BTN_TL2",
        0x139: "BTN_TR2",
        0x13a: "BTN_SELECT",
        0x13b: "BTN_START",
        0x13c: "BTN_MODE",
        0x13d: "BTN_THUMBL",
        0x13e: "BTN_THUMBR",
        0x140: "BTN_TOOL_PEN",
        0x141: "BTN_TOOL_RUBBER",
        0x142: "BTN_TOOL_BRUSH",
        0x143: "BTN_TOOL_PENCIL",
        0x144: "BTN_TOOL_AIRBRUSH",
        0x145: "BTN_TOOL_FINGER",
        0x146: "BTN_TOOL_MOUSE",
        0x147: "BTN_TOOL_LENS",
        0x14a: "BTN_TOUCH",
        0x14b: "BTN_STYLUS",
        0x14c: "BTN_STYLUS2",
        }),

        "EV_REL": EnumDict({
        0x00: "REL_X",
        0x01: "REL_Y",
        0x02: "REL_Z",
        0x06: "REL_HWHEEL",
        0x07: "REL_DIAL",
        0x08: "REL_WHEEL",
        0x09: "REL_MISC",
        }),

        "EV_ABS": EnumDict({
        0x00: "ABS_X",
        0x01: "ABS_Y",
        0x02: "ABS_Z",
        0x03: "ABS_RX",
        0x04: "ABS_RY",
        0x05: "ABS_RZ",
        0x06: "ABS_THROTTLE",
        0x07: "ABS_RUDDER",
        0x08: "ABS_WHEEL",
        0x09: "ABS_GAS",
        0x0a: "ABS_BRAKE",
        0x10: "ABS_HAT0X",
        0x11: "ABS_HAT0Y",
        0x12: "ABS_HAT1X",
        0x13: "ABS_HAT1Y",
        0x14: "ABS_HAT2X",
        0x15: "ABS_HAT2Y",
        0x16: "ABS_HAT3X",
        0x17: "ABS_HAT3Y",
        0x18: "ABS_PRESSURE",
        0x19: "ABS_DISTANCE",
        0x1a: "ABS_TILT_X",
        0x1b: "ABS_TILT_Y",
        0x1c: "ABS_MISC",
        }),

        "EV_MSC": EnumDict({
        0x00: "MSC_SERIAL",
        0x01: "MSC_PULSELED",
        }),

        "EV_LED": EnumDict({
        0x00: "LED_NUML",
        0x01: "LED_CAPSL",
        0x02: "LED_SCROLLL",
        0x03: "LED_COMPOSE",
        0x04: "LED_KANA",
        0x05: "LED_SLEEP",
        0x06: "LED_SUSPEND",
        0x07: "LED_MUTE",
        0x08: "LED_MISC",
        }),

        "EV_REP": EnumDict({
        0x00: "REP_DELAY",
        0x01: "REP_PERIOD",
        }),

        "EV_SND": EnumDict({
        0x00: "SND_CLICK",
        0x01: "SND_BELL",
        }),
        }

    def __init__(self, timestamp=0, type=0, code=0, value=0, unpack=None, readFrom=None):
        self.timestamp = timestamp
        self.type = type
        self.code = code
        self.scanCode = -1
        self.value = value
        if unpack is not None:
            self.unpack(unpack)
        if readFrom is not None:
            self.readFrom(readFrom)

    def __repr__(self):
        return "<Event timestamp=%r type=%r code=%r value=%r>" % (
            self.timestamp, self.type, self.code, self.value)
    
    @staticmethod
    def get_format_size():
        return struct.calcsize(Event.ts_format) + struct.calcsize(Event.format)
    
    def pack(self):
        """Pack this event into an input_event struct in
           the local machine's byte order.
           """
        secs = int(self.timestamp)
        usecs = int((self.timestamp - secs) * 1000000)
        packedType = self.typeMap.toNumber(self.type)
        if self.type in self.codeMaps:
            packedCode = self.codeMaps[self.type].toNumber(self.code)
        else:
            packedCode = self.code
        return struct.pack(self.ts_format, secs, usecs) + \
               struct.pack(self.format, packedType, packedCode, self.value)

    def unpack(self, s):
        """Unpack ourselves from the given string,, an
           input_event struct in the local byte order.
           """
        ts_len = struct.calcsize(self.ts_format)
        secs, usecs = struct.unpack(self.ts_format, s[:ts_len])
        packedType, packedCode, self.value = struct.unpack(self.format, s[ts_len:])
        self.timestamp = secs + (usecs / 1000000.0)
        self.type = self.typeMap.fromNumber(packedType)
        if self.type in self.codeMaps:
            self.code = self.codeMaps[self.type].fromNumber(packedCode)
        else:
            self.code = packedCode
        self.scanCode = packedCode

    def readFrom(self, stream):
        """Read the next event from the given file-like object"""
        self.unpack(stream.read(Event.get_format_size()))


if __name__ == "__main__":
    demo()

### The End ###
