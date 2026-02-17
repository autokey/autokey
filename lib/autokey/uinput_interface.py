#  Copyright (C) 2024  @sebastiansam55 on GitHub.com
#  Copyright (C) 2026  David King <dave@daveking.com>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License,
#  version 2, as published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License,
#  version 2, along with this program; if not, see 
#  <https://www.gnu.org/licenses/old-licenses/gpl-2.0.html>.
#
#####################################################################

# items avaliable on inputevents
# https://python-evdev.readthedocs.io/en/latest/apidoc.html#evdev.events.InputEvent
# sec, usec, type, code, value

import typing
import threading
import queue
import os
import grp
import evdev
#  @dlk3 - support multiple keyboards/mice
import pyudev
import time
import select
import random
import re
import pathlib
import subprocess

from autokey.model.button import Button
from autokey.model.phrase import SendMode
from autokey.model.key import Key

import evdev
from evdev import ecodes as e

from autokey.autokey_app import AutokeyApplication

logger = __import__("autokey.logger").logger.get_logger(__name__)

from autokey.sys_interface.abstract_interface import AbstractSysInterface, AbstractMouseInterface, queue_method
import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants
from autokey.gnome_interface import GnomeMouseReadInterface

#TODO when exiting the thread waits for one more signal and that signal repeats  for a bit during exit
#  @dlk3 I put a timeout on the select in __flush_events() so that it would not
#  block forever waiting for a keypress after a self.ui device has been closed.
#  This matches how things are done in the equivalent function in the X11
#  interface.py module.

class UInputInterface(threading.Thread, GnomeMouseReadInterface, AbstractSysInterface):
    """
    god this is complicated lol
    """

    inv_map = {}
    char_map = {
        "/":"KEY_SLASH", "'":"KEY_APOSTROPHE", ",":"KEY_COMMA", ".":"KEY_DOT", ";":"KEY_SEMICOLON",
        "[":"KEY_LEFTBRACE", "]":"KEY_RIGHTBRACE", "\\":"KEY_BACKSLASH", "=":"KEY_EQUAL", "-":"KEY_MINUS", "`": "KEY_GRAVE",
        " ":"KEY_SPACE", "\t": "KEY_TAB","\n": "KEY_ENTER"
    }
    #define as the left versions
    shift_key = 42
    ctrl_key = 29
    alt_key = 56
    meta_key = 125
    #TODO other modifiers
    #altgr_key
    #TODO should this be raw scan code or evdev equivalent? evdev makes more sense to me here
    #string.printable;
    #0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r\x0b\x0c
    #
    shifted_chars = {
        "!":"KEY_1", "@":"KEY_2", "#":"KEY_3", "$":"KEY_4", "%":"KEY_5", "^":"KEY_6", "&": "KEY_7", "*": "KEY_8", "(":"KEY_9", ")":"KEY_0",
        "\"":"KEY_APOSTROPHE", ">": "KEY_DOT", "<": "KEY_COMMA", ":":"KEY_SEMICOLON", "{": "KEY_LEFTBRACE", "}": "KEY_RIGHTBRACE",
        "?": "KEY_SLASH", "+": "KEY_EQUAL", "_":"KEY_MINUS", "~":"KEY_GRAVE", "|":"KEY_BACKSLASH"
    }

    """
    str(AutoKey): str(evdev KEY_XXXX)
    """
    autokey_map = {
        "<left>": "KEY_LEFT", "<right>": "KEY_RIGHT", "<up>": "KEY_UP", "<down>": "KEY_DOWN",
        "<home>": "KEY_HOME", "<end>": "KEY_END", "<page_up>": "KEY_PAGEUP", "<page_down>": "KEY_PAGEDOWN",

        # universal modifiers
        "<shift>": "KEY_LEFTSHIFT", "<ctrl>": "KEY_LEFTCTRL", "<alt>": "KEY_LEFTALT",
        "<meta>": "KEY_LEFTMETA", "<hyper>": "KEY_LEFTMETA", "<super>": "KEY_LEFTMETA",

        # left modifiers
        "<left_shift>": "KEY_LEFTSHIFT", "<left_ctrl>": "KEY_LEFTCTRL", "<left_alt>": "KEY_LEFTALT", "<left_meta>": "KEY_LEFTMETA", "<left_hyper>": "KEY_LEFTMETA",

        # right modifiers
        "<right_shift>": "KEY_RIGHTSHIFT", "<right_ctrl>": "KEY_RIGHTCTRL", "<right_alt>": "KEY_RIGHTALT", "<right_meta>": "KEY_RIGHTMETA", "<right_hyper>": "KEY_RIGHTMETA",

        "<backspace>": "KEY_BACKSPACE",


        "<enter>": "KEY_ENTER", "\n": "KEY_ENTER",
        "<tab>": "KEY_TAB", "\t": "KEY_TAB",
        "<escape>": "KEY_ESCAPE"
    }

    """
    str(evdev KEY_XXXX): str(AutoKey)
    """
    inv_autokey_map = {}

    uinput_modifiers_to_ak_map = {

        "KEY_LEFTSHIFT" : Key.LEFTSHIFT,
        "KEY_RIGHTSHIFT" : Key.RIGHTSHIFT,

        "KEY_LEFTCTRL": Key.LEFTCONTROL,
        "KEY_RIGHTCTRL": Key.RIGHTCONTROL,

        "KEY_LEFTALT": Key.LEFTALT,
        "KEY_RIGHTALT": Key.RIGHTALT,

        "KEY_LEFTMETA": Key.LEFTMETA,
        "KEY_RIGHTMETA": Key.RIGHTMETA,

    }

    uinput_keys_to_ak_map = {
        "KEY_LEFT": Key.LEFT,
        "KEY_RIGHT": Key.RIGHT,
        "KEY_UP": Key.UP,
        "KEY_DOWN": Key.DOWN,

        "KEY_HOME": Key.HOME,
        "KEY_END": Key.END,
        "KEY_PAGEUP": Key.PAGE_UP,
        "KEY_PAGEDOWN": Key.PAGE_DOWN,

        "KEY_BACKSPACE": Key.BACKSPACE,

        "KEY_ENTER": Key.ENTER,
        "KEY_TAB": Key.TAB,

        "KEY_ESC": Key.ESCAPE,

        "KEY_F1": Key.F1,
        "KEY_F2": Key.F2,
        "KEY_F3": Key.F3,
        "KEY_F4": Key.F4,
        "KEY_F5": Key.F5,
        "KEY_F6": Key.F6,
        "KEY_F7": Key.F7,
        "KEY_F8": Key.F8,
        "KEY_F9": Key.F9,
        "KEY_F10": Key.F10,
        "KEY_F11": Key.F11,
        "KEY_F12": Key.F12,

    }


    translation_map = {
        "slash": "/", "apostrophe": "'", "comma": ",", "dot": ".", "semicolon": ";",
        "space": " ", "tab": "\t", "enter": "\n",
        "backslash": "\\", "equal": "=", "minus": "-", "grave": "`",
    }

    #TODO complete this
    btn_map = {
        Button.LEFT: [e.BTN_LEFT, 0x90001],
        Button.RIGHT: [e.BTN_RIGHT, 0x90002],
        Button.MIDDLE: [e.BTN_MIDDLE, 0x90003],
        #4: [e.BTN_SIDE, 0x90004],
        #5: [e.BTN_EXTRA, 0x90005],
        #6: [],
        #7: [],
        #8: [e.BTN_BACK, ]

    }
    inv_btn_map = {
        "BTN_LEFT": Button.LEFT,
        "BTN_RIGHT": Button.RIGHT,
        "BTN_MIDDLE": Button.MIDDLE
    }

    queue = queue.Queue()

    def __init__(self, mediator, app):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("UInputInterface-thread")
        self.mediator = mediator  #  type - IoMediator
        self.app = app            #  type - AutokeyApplication
        self.shutdown = False
        self.sending = False
        #  @dlk3 - support multiple keyboards/mice
        self.keyboards = []
        self.mice = []
        self.device_paths = []
        #self.keyboard = None
        #self.mouse = None
        self.capabilities = None
        time.sleep(1)

        # Event loop
        self.eventThread = threading.Thread(target=self.__eventLoop)

        ### UINPUT init
        self.validate()

        #self.grab_devices()

        # @dlk3 - support multiple keyboards/mice
        self.grab_multiple_devices()
        logger.debug("The following devices are available on this system:\n\t{}".format('\n\t'.join([ dev.name for dev in self.get_devices() ])))
        logger.debug("I grabbed these devices from that list: \n\t{}".format('\n\t'.join([ dev.name for dev in self.keyboards + self.mice ])))
        self.__watch_for_new_devices()

        try:
            # mouse = "/dev/input/event12"
            # keyboard = "/dev/input/event4"
            # creating a uinput device with the combined capabilities of the user's mouse and keyboard
            # this will undoubtedly cause issues if user attempts to send signals not supported by their devices
            self.ui = evdev.UInput.from_device(*self.device_paths, name="autokey mouse and keyboard")
            self.capabilities = self.ui.capabilities(verbose=True)
            logger.debug("UInput device capabilities: {}".format(self.capabilities))
            logger.info("Supports ABS Movement: {}".format(self.supports_abs()))
            logger.info("Supports REL Movement: {}".format(self.supports_rel()))
        except Exception as ex:
            logger.error("Unable to create UInput device. {}".format(ex))
            logger.error("Check out how to resolve this issue here: https://github.com/philipl/evdevremapkeys/issues/24")
            raise Exception
            #print("Unable to create UInput device. {}".format(ex))

        GnomeMouseReadInterface.__init__(self)
        logger.debug("Screen size: {}".format(self.mediator.windowInterface.get_screen_size()))

        self.inv_map = self.__reverse_mapping(e.keys)
        self.inv_autokey_map = self.__reverse_mapping(self.autokey_map)
        logger.debug("Inverted Map:", self.inv_map)

        # Event listener
        self.listenerThread = threading.Thread(target=self.__flush_events_loop)

        self.__initMappings()

        self.eventThread.start()
        self.listenerThread.start()

    #  @dlk3 - support multiple keyboards/mice
    #  Watch for new USB or Bluetooth devices to be added to the system and rerun
    #  grab_multiple_devices() and reset the fake uinput device when they are
    def __watch_for_new_devices(self):
        #  Handler runs in its own thread when it's invoked by monitor
        def event_handler(action, device):
            if action == 'bind':
                logger.info("UDEV reports that a new device was added to the system, checking to see if it is a keyboard or mouse that I should grab.")
                self.grab_multiple_devices()
                self.ui = evdev.UInput.from_device(*self.device_paths, name="autokey mouse and keyboard")
                logger.debug("Devices that I've grabbed: \"{}\"".format('\", \"'.join([ dev.name for dev in self.keyboards + self.mice ])))

        monitor = pyudev.Monitor.from_netlink(pyudev.Context())

        #  Tell the monitor that we only want to see events from these UDEV "subsystems"
        monitor.filter_by('usb')
        monitor.filter_by('hidraw')  # Covers bluetooth devices, I think. I can't test this, I don't have any bluetooth keyboards/mice.

        self.udev_observer = pyudev.MonitorObserver(monitor, event_handler)
        self.udev_observer.start()

    #  @dlk3 - support multiple keyboards/mice
    def grab_multiple_devices(self):
        ### UINPUT Listener one for keyboard and eventually one for mouse
        # creating this before creating the new uinput device !important
        devices = self.get_devices()

        for dev in devices:
            #logger.debug(f"Found device: {dev.name}")
            #  Close any existing fake uinput devices, which would likely
            #  be the result of some sort of crash during a prior run.
            if dev.name == 'autokey mouse and keyboard':
                self.ui.close()
                continue
            #  Ignore devices we already grabbed during prior calls to this method
            if dev.path in self.device_paths:
                #logger.debug('This device has already been grabbed')
                continue

            if re.search("keyboard", dev.name, re.IGNORECASE):
                try:
                    #logger.debug("Device has the word \"keyboard\" as part of its name, grabbing it.")
                    keyboard = self.grab_device(devices, dev.name)
                    keyboard.grab()
                    self.keyboards.append(keyboard)
                    self.device_paths.append(keyboard.path)
                    #logger.debug("Keyboard: {}, Path: {}".format(keyboard.name, keyboard.path))
                except Exception as error:
                    logger.error(f"Could not grab keyboard device \"{dev.name}\" from list of devices found on system: {error}")
            elif re.search("mouse", dev.name, re.IGNORECASE):
                try:
                    #logger.debug("Device has the word \"mouse\" as part of its name, grabbing it.")
                    mouse = self.grab_device(devices, dev.name)
                    self.mice.append(mouse)
                    self.device_paths.append(mouse.path)
                    #logger.debug("Mouse: {}, Path: {}".format(mouse.name, mouse.path))
                except Exception as error:
                    logger.error(f"Could not grab mouse device  \"{dev.name}\" from list of devices found on system: {error}")
            elif dev.name in cm.ConfigManager.SETTINGS[cm_constants.KEYBOARD]:
                try:
                    #logger.debug("Device name matches a keyboard listed in the config file, grabbing it.")
                    keyboard = self.grab_device(devices, dev.name)
                    keyboard.grab()
                    self.keyboards.append(keyboard)
                    self.device_paths.append(keyboard.path)
                    #logger.debug("Keyboard: {}, Path: {}".format(keyboard.name, keyboard.path))
                except Exception as error:
                    logger.error(f"Could not grab keyboard device \"{dev.name}\" from configuration settings: {error}")
            elif dev.name in cm.ConfigManager.SETTINGS[cm_constants.MOUSE]:
                try:
                    #logger.debug("Device name matches a mouse listed in the config file, grabbing it.")
                    mouse = self.grab_device(devices, dev.name)
                    self.mice.append(mouse)
                    self.device_paths.append(mouse.path)
                    #logger.debug("Mouse: {}, Path: {}".format(mouse.name, mouse.path))
                except Exception as error:
                    logger.error(f"Could not grab mouse device \"{dev.name}\" from configuration settings: {error}")

        dev_list = "\n(I could not get the list of devices.  Please press \"Esc\", log off and back on, and try running AutoKey again."
        if len(self.keyboards) == 0:
            logger.error(f"Unable to find a keyboard to connect to")
            dev_list = ''
            if len(devices) > 0:
                for dev in devices:
                    dev_list = dev_list + '\n' + dev.name
            self.app.show_error_dialog_with_link(f"Unable to connect a keyboard device", f"I am unable to recognize your keyboard device.  Please update the \"keyboard\" and \"mouse\" lists in the AutoKey configuration file {cm_constants.CONFIG_FILE} with the name(s) of your keyboard and mouse device(s) from this list:\n{dev_list}\n\nClick the \"Open\" button below to edit the configuration file now or simply press \"Esc\" to close this message.", link_data=cm_constants.CONFIG_FILE)
            exit(1)
        if len(self.mice) == 0:
            logger.error(f"Unable to find a mouse to connect to")
            dev_list = ''
            if len(devices) > 0:
                for dev in devices:
                    dev_list = dev_list + '\n' + dev.name
            self.app.show_error_dialog_with_link(f"Unable to connect a mouse device", f"I am unable to recognize your mouse device.  Please update the \"keyboard\" and \"mouse\" lists in the AutoKey configuration file {cm_constants.CONFIG_FILE} with the name(s) of your keyboard and mouse device(s) from this list:\n{dev_list}\n\nClick the \"Open\" button below to edit the configuration file now or simply press \"Esc\" to close this message.", link_data=cm_constants.CONFIG_FILE)
            exit(1)

        self.devices = self.keyboards + self.mice
        self.devices = {dev.fd: dev for dev in self.devices}

    def supports_abs(self):
        has_abs_x = False
        has_abs_y = False
        if self.capabilities and self.capabilities.get(('EV_ABS', 3)):
            for item in self.capabilities[('EV_ABS', 3)]:
                if item[0][0] == 'ABS_X':
                    has_abs_x = True
                if item[0][0] == 'ABS_Y':
                    has_abs_y = True
            return has_abs_x and has_abs_y
        return False

    def supports_rel(self):
        has_rel_x = False
        has_rel_y = False

        if self.capabilities.get(('EV_REL', 2)):
            for item in self.capabilities[('EV_REL', 2)]:
                if item[0] == 'REL_X':
                    has_rel_x = True
                if item[0] == 'REL_Y':
                    has_rel_y = True
            return has_rel_x and has_rel_y
        return False

    def __reverse_mapping(self, dictionary):
        map = {}
        for item in dictionary.items():
            if type(item[1]) == list:
                continue
            else:
                map[item[1]] = item[0]
        return map

    def validate(self):
        """
        Checks that UInput will work correctly

        Prints out error message currently if that fails.
        """
        user = os.getlogin()
        input_group = grp.getgrnam("input")
        if user in input_group.gr_mem or os.geteuid()==0:
            logger.info(f"{user} is a member of the \"input\" user group")
        else:
            msg = f"{user} is not in the \"input\" user group."
            logger.error(msg + f"  Add yourself:\nsudo usermod -a -G input {user}")
            raise Exception(msg)

    @queue_method(queue)
    def send_mouse_click(self, xCoord, yCoord, button: Button, relative):
        self.move_cursor(xCoord, yCoord, relative)

        keycode = self.btn_map[button][0]
        scancode = self.btn_map[button][1]

        self.ui.write(e.EV_MSC, e.MSC_SCAN, scancode)
        self.ui.write(e.EV_KEY, keycode, 1)
        self.syn_raw()

        self.ui.write(e.EV_MSC, e.MSC_SCAN, scancode)
        self.ui.write(e.EV_KEY, keycode, 0)
        self.syn_raw()

    @queue_method(queue)
    def mouse_press(self, xCoord, yCoord, button):
        self.move_cursor(xCoord, yCoord)

        keycode = self.btn_map[button][0]
        scancode = self.btn_map[button][1]

        self.ui.write(e.EV_MSC, e.MSC_SCAN, scancode)
        self.ui.write(e.EV_KEY, keycode, 1)
        self.syn_raw()

    @queue_method(queue)
    def mouse_release(self, xCoord, yCoord, button):
        self.move_cursor(xCoord, yCoord)

        keycode = self.btn_map[button][0]
        scancode = self.btn_map[button][1]

        self.ui.write(e.EV_MSC, e.MSC_SCAN, scancode)
        self.ui.write(e.EV_KEY, keycode, 0)
        self.syn_raw()

    # implemented in GnomeMouseReadInterface
    # def mouse_location(self):
    #     raise NotImplementedError

    def relative_mouse_location(self, window=None):
        mousex,mousey = self.mouse_location()
        if window is None:
            window = self.mediator.windowInterface.get_active_window()
        winx = window.get('x')
        winy = window.get('y')
        relx = mousex - winx
        rely = mousey - winy

        return (relx, rely)

    @queue_method(queue)
    def scroll_down(self, number):
        for i in range(number):
            self.ui.write(e.EV_REL, e.REL_WHEEL, -1)
            self.ui.write(e.EV_REL, e.REL_WHEEL_HI_RES, -120)
            self.syn_raw()

    @queue_method(queue)
    def scroll_up(self, number):
        for i in range(number):
            self.ui.write(e.EV_REL, e.REL_WHEEL, 1)
            self.ui.write(e.EV_REL, e.REL_WHEEL_HI_RES, 120)
            self.syn_raw()

    @queue_method(queue)
    def move_cursor(self, xCoord, yCoord, relative=False, relative_self=False):
        #TODO implement relative
        if relative or relative_self:
            raise NotImplementedError
        current_x, current_y = self.mouse_location()
        screen_x, screen_y = self.mediator.windowInterface.get_screen_size()
        count = 0
        max_count = 1000
        xstep = 200
        ystep = 200
        range1 = 200
        range2 = 10

        # check that REL is supported
        if not self.supports_rel():
            raise RuntimeError("Need REL support")

        while True:
            logger.debug(f"Current X: {current_x}, Current Y: {current_y}, xstep: {xstep}, ystep:{ystep}")

            if current_x == xCoord and current_y == yCoord:
                logger.debug(f"Took {count} steps")
                break

            #xstep logic
            if xstep==200 and (current_x <= xCoord+range1 and current_x >= xCoord-range1):
                logger.debug(f"Changing xstep to 10 at {current_x} within 100 of {xCoord} [{xCoord-range1},  {xCoord+range1}]")
                xstep = 10
            if xstep==10 and (current_x <= xCoord+range2 and current_x >= xCoord-range2):
                logger.debug(f"Changing xstep to 1 at {current_x} within 10 of {xCoord} [{xCoord-range2},  {xCoord+range2}]")
                xstep = 1

            #x move
            # REL_X - X axis, positive is right, negative is left.
            if current_x < xCoord: self.ui.write(e.EV_REL, e.REL_X, xstep)
            elif current_x > xCoord: self.ui.write(e.EV_REL, e.REL_X, -xstep)

            #ystep logic
            if ystep==200 and (current_y <= yCoord+range1 and current_y >= yCoord-range1):
                logger.debug(f"Changing ystep to 10 at {current_y} within 100 of {yCoord} [{yCoord-range1},  {yCoord+range1}]")
                ystep = 10
            if ystep==10 and (current_y <= yCoord+range2 and current_y >= yCoord-range2):
                logger.debug(f"Changing ystep to 1 at {current_y} within 10 of {yCoord} [{yCoord-range2},  {yCoord+range2}]")
                ystep = 1

            #y move
            # REL_Y - Y axis, positive is down, negative is up.
            if current_y < yCoord: self.ui.write(e.EV_REL, e.REL_Y, ystep)
            elif current_y > yCoord: self.ui.write(e.EV_REL, e.REL_Y, -ystep)

            self.syn_raw()
            current_x, current_y = self.mouse_location()

            #prevent inf looping from bad logic
            count = count+1
            if count > max_count:
                break

    def send_mouse_click_relative(self, xoff, yoff, button):
        x,y = self.mouse_location()
        self.send_mouse_click(x+xoff, y+yoff, button)

    @queue_method(queue)
    def clear_held_keys(self):
        #self.held_keys = self.keyboard.active_keys()
        # @dlk3  - mutiple devices fix
        self.held_keys = []
        for keyboard in self.keyboards:
            self.held_keys = self.held_keys + keyboard.active_keys(verbose=True)

        logger.debug("Clearing keys: {}".format(self.held_keys))
        for key in self.held_keys:
            self.ui.write(e.EV_KEY, key, 0)

    @queue_method(queue)
    def reapply_keys(self):
        #self.held_keys = self.keyboard.active_keys()
        logger.debug("Reapply held keys: {}".format(self.held_keys))
        for key in self.held_keys:
            self.ui.write(e.EV_KEY, key, 1)


    @queue_method(queue)
    def send_string(self, string):
        """
        Send a string of characters to be sent via the keyboard
        Usage: C{ukeyboard.send_keys("This is a test string")}
        :param string: str or list, use list if you want to send characters like KEY_LEFTCTRL
        """
        #print(keys)
        # if type(string) == list:
        #     for subset in string:
        #         self.send_string(subset)
        #     return
        if type(string) == str and "KEY_" in string[:4]:
            self.__send_key(string)
            return
        if type(string) == int:
            self.__send_key(string)
            return

        for key in string:
            self.__send_key(key)

    def paste_string(self, string, paste_command: SendMode):
        raise NotImplementedError

    @queue_method(queue)
    def send_key(self, key_name):
        self.__send_key(key_name)

    @queue_method(queue)
    def send_evdev_code(self, type_, code, value):
        self.ui.write(type_, code, value)

    def send_evdev_code_raw(self, type_, code, value):
        """
        Immediately sends the event instead of adding it to the queue.
        """
        self.ui.write(type_, code, value)

    def __send_key(self, key, shifted=False, syn=True):
        # print(f"Writing {key}")
        evdev_keycode, shifted_ = self.translate_to_evdev(key)
        #print(key, evdev_keycode, shifted_)
        evdev_key = e.keys[evdev_keycode]
        if shifted_:
            shifted=True

        #print(f"Keycode: {evdev_keycode}, Key: {evdev_key}", shifted_, shifted)
        logger.debug("Sending key: {}, Shifted: {}, Untranslated: {}".format(evdev_key, shifted_, key))
        if shifted:
            self.ui.write(e.EV_MSC, e.MSC_SCAN, self.shift_key)
            self.ui.write(e.EV_KEY, self.shift_key, 1)
            self.syn_raw()

        self.ui.write(e.EV_MSC, e.MSC_SCAN, self.inv_map[evdev_key])
        self.ui.write(e.EV_KEY, self.inv_map[evdev_key], 1)
        if syn : self.syn_raw()

        self.ui.write(e.EV_MSC, e.MSC_SCAN, self.inv_map[evdev_key])
        self.ui.write(e.EV_KEY, self.inv_map[evdev_key], 0)
        if syn : self.syn_raw()

        if shifted:
            self.ui.write(e.EV_MSC, e.MSC_SCAN, self.shift_key)
            self.ui.write(e.EV_KEY, self.shift_key, 0)
            self.syn_raw()

    def get_delay(self):
        #TODO does this need to be cached?
        return float(cm.ConfigManager.SETTINGS[cm_constants.DELAY])/1000

    @queue_method(queue)
    def syn(self):
        self.ui.write(e.EV_SYN, 0, 0)
        time.sleep(self.get_delay()) #important to sleep here, otherwise the modifiers can be lost

    def syn_raw(self):
        self.ui.write(e.EV_SYN, 0, 0)
        time.sleep(self.get_delay()) #important to sleep here, otherwise the modifiers can be lost

    @queue_method(queue)
    def press_key(self, keyName):
        self.__press_key(keyName, True)

    @queue_method(queue)
    def release_key(self, keyName):
        self.__release_key(keyName, True)

    def __release_key(self, key, syn=False):
        evdev_keycode, shifted_ = self.translate_to_evdev(key)
        #print(key, evdev_keycode, shifted_)
        evdev_key = e.keys[evdev_keycode]
        if shifted_:
            shifted=True

        self.ui.write(e.EV_MSC, e.MSC_SCAN, self.inv_map[evdev_key])
        self.ui.write(e.EV_KEY, self.inv_map[evdev_key], 0)
        if syn: self.syn_raw()

    def  __press_key(self, key, syn=False):
        evdev_keycode, shifted_ = self.translate_to_evdev(key)
        #print(key, evdev_keycode, shifted_)
        evdev_key = e.keys[evdev_keycode]
        if shifted_:
            shifted=True
        self.ui.write(e.EV_MSC, e.MSC_SCAN, self.inv_map[evdev_key])
        self.ui.write(e.EV_KEY, self.inv_map[evdev_key], 1)
        if syn: self.syn_raw()


    # def wait_for_keypress(self, timeout=None):
    #     raise NotImplementedError


    # def wait_for_keyevent(self, timeout=None):
    #     raise NotImplementedError

    def __initMappings(self):
        """
        Grabs hotkeys. Under X11 this means blocking the hotkeys from sending to individual applications.
        Not sure if this can be accomplished via uinput/wayland?

        @dlk3 - It needs to be done and I added code to suppress hotkeys being
        sent though to apps at the end of the __flush_events() method below.
        """
        self.__grab_hotkeys()

    def __grab_hotkeys(self):
        self.__grab_ungrab_all_hotkeys(grab=True)

    def __ungrab_all_hotkeys(self):
        self.__grab_ungrab_all_hotkeys(grab=False)
        self.hotkeys = []

    def __grab_ungrab_all_hotkeys(self, grab=True):
        c = self.app.configManager
        logger.debug("Starting UInput hotkey grabber:")
        hotkeys = c.hotKeys + c.hotKeyFolders

        for item in hotkeys:
            if "code" in item.hotKey:
                #this implies that it is a legacy x11 keycode, should we try to remap?
                # not sure that this would be possible/practical
                # need to tell the user this is an issue
                self.app.show_error_dialog(f"Detected Legacy x11 keycode {item.hotKey} for {item}", )
                # TODO: for some reason the above will prevent the rest of the application from starting?
                logger.warning(f"Detected likely invalid hotkey: {item}")
                #from interface import XK_TO_AK_MAP

                pass
            logger.debug("Hotkey: {}, Modifier: {}".format(item.hotKey, item.modifiers))

    def isModifier(self, keyCode):
        """
        """
        for item in self.uinput_modifiers_to_ak_map:
            if item == keyCode:
                logger.debug("isModifier: {}, True".format(keyCode))
                return True
        logger.debug("isModifier: {}, False".format(keyCode))
        return False
        # if keyCode in self.uinput_to_ak_map:
            # return True
        # print(keyCode, self.modifiers, self.translate_to_evdev(keyCode))
        # print(self.inv_map[keyCode[1]])

    @queue_method(queue)
    def handle_keypress(self, keyCode):
        window_info = self.mediator.windowInterface.get_window_info()
        event_type = evdev.categorize(keyCode)
        logger.debug("handle_keypress: KeyState:{}, Un:{}".format(event_type.keystate, event_type.keycode))
        if self.isModifier(event_type.keycode):
            # need to translate event_type.keycode to a Key. value from an evdev keycode
            self.mediator.handle_modifier_down(self.uinput_modifiers_to_ak_map[event_type.keycode])
        # else:
            # self.mediator.handle_keypress(self.translate_to_evdev(event_type.keycode), window_info)

    @queue_method(queue)
    def handle_keyrelease(self, keyCode):
        window_info = self.mediator.windowInterface.get_window_info()
        event_type = evdev.categorize(keyCode)
        logger.debug("handle_keyrelease: KeyState:{}, Un:{}".format(event_type.keystate, event_type.keycode))
        if self.isModifier(event_type.keycode):
            self.mediator.handle_modifier_up(self.uinput_modifiers_to_ak_map[event_type.keycode])
        else:
            self.mediator.handle_keypress(self.translate_to_evdev(event_type.keycode), window_info)

    def __flush_events_loop(self):
        logger.debug("__flushEvents: Entering event loop.")
        while True:
            try:
                #logger.debug("__flushEvents: Waiting for events.")
                self.__flush_events()
                if self.shutdown:
                    break
            except Exception as e:
                logger.exception(
                    "Some exception occurred in the flush events loop: {}".format(e))
        logger.debug("Left event loop.")

    def __flush_events(self):
        #  @dlk3 select needs a timeout or it hangs when a new input device is added to self.devices
        r,w,x = select.select(self.devices, [], [], 1)
        for fd in r:
            if not pathlib.Path(self.devices[fd].path).exists():
                # @dlk3 - multidevice fix - remove the missing device from the lists and redefine the fake uinput device
                logger.info(f"The \"{self.devices[fd].name}\" device has dissappeared from the system.")
                self.device_paths.remove(self.devices[fd].path)
                self.devices.pop(fd)

                if len(self.devices) == 0:
                    logger.error("The last keyboard/mouse input device has been removed from the system")
                    self.app.show_error_dialog(f"Last keyboard/mouse removed", details="The last keyboard/mouse has been removed from the system.  There's no reason for AutoKey to keep running so I'll be saying \"Bye, bye.\"")
                    self.shutdown = True
                    return

                keyboards_list = []
                for keyboard in self.keyboards:
                    if keyboard.fd != fd:
                        keyboards_list.append(keyboard)
                self.keyboards = keyboards_list

                mouse_list = []
                for mouse in self.mice:
                    if mouse.fd != fd:
                        mouse_list.append(mouse)
                self.mice = mouse_list

                self.ui.close()
                self.ui = evdev.UInput.from_device(*self.device_paths, name="autokey mouse and keyboard")
                continue
            for event in self.devices[fd].read(): # type: ignore
                event_type = evdev.categorize(event)
                # @dlk3  - mutiple devices fix
                held = []
                for keyboard in self.keyboards:
                    held = held + keyboard.active_keys(verbose=True)

                if type(event_type) is evdev.KeyEvent:

                    # if event_type.scancode in iter(Button): #is a mouse button
                        # continue
                        #logger.debug("__flush_events: Button State: {}, Button Code: {}".format(event_type.keystate, event_type.keycode))

                    if event_type.keystate == 1 : #key down
                        logger.debug("__flush_events: Key State: {}, Key Code: {}, Scan Code: {}".format(event_type.keystate, event_type.keycode, event_type.scancode))
                        logger.debug("Held: {}".format(held))
                        #logger.debug("Key: {}".format(event_type))
                        self.handle_keypress(event)
                    elif event_type.keystate == 0: #key up
                        self.handle_keyrelease(event)
                    elif event_type.keystate == 2: # hold event
                        #TODO: handle hold event
                        pass
                    #TODO can also handle scroll events here

                    if event_type.keycode == 'KEY_ESC' and event_type.keystate == 1:
                        #TODO implement. I think we'd need to break out into a separate input and send queue.
                        # logger.info("Escape key pressed. Clearing the queue.")
                        #self.clear_queue()
                        pass

                elif type(event_type) is evdev.RelEvent:
                    pass
                    #TODO: mouse movement event
                    #logger.debug("Mouse: {}".format(event_type))
                    #if event_type.
                    #self.handle_mouseclick(event)

                # dlk3 - the following self.ui.write sends through AutoKey hotkeys,
                # which it shouldn't do, so we'll return now, before that happens,
                # if the "held" list holds an AutoKey hotkey
                if self.__isAutoKeyHotkey(held):
                    return

                # dlk3 - support multiple keyboards/mice
                # pass through to autokey uinput device
                for keyboard in self.keyboards:
                    if not self.sending and fd == keyboard.fd:
                        self.ui.write(event.type, event.code, event.value)

    #  @dlk3 - Does the list of keys from __flush_events() match an AutoKey hotkey?
    def __isAutoKeyHotkey(self, key_list):
        #  If the key_list passed to us doesn't contain at least two keys
        #  then it can't be a hot key
        if len(key_list) < 2:
            return False

        #  Convert the key_list from a list of tuples to a simple list of key codes:
        key_list = [ x[1] for x in key_list ]
        key_list.sort()

        #  Check each AutoKey hotkey contained in the configuration
        for item in self.app.configManager.hotKeys + self.app.configManager.globalHotkeys:

            #  If this hotkey has a window filter which doesn't match the active
            #  window it can't be a match, iterate the loop.
            if item.windowInfoRegex != None:
                window_info = self.mediator.windowInterface.get_window_info()
                if not item.windowInfoRegex.match(window_info.wm_title):
                    continue

            #  Convert this hotkey from a list of tuples to a simple list of
            #  key codes so that we can compare it to the key_list
            hotkey_codes = [self.translate_to_evdev(item.hotKey)]
            for modifier in item.modifiers:
                hotkey_codes.append(self.translate_to_evdev(modifier))
            hotkey_codes = [ x[0] for x in hotkey_codes ]
            hotkey_codes.sort()

            #  Check if the hotkey_codes match the key_list we received
            #logger.debug(f"Will block hotkey if key_list: {key_list} == hotkey_codes: {hotkey_codes}")
            if key_list == hotkey_codes:
                return True

        return False

    # def clear_queue(self):
    #     """Clear the current queue of events."""
    #     while not self.queue.empty():
    #         try:
    #             self.queue.get_nowait()
    #             self.queue.task_done()
    #         except queue.Empty:
    #             break
    #     logger.info("Queue cleared.")

    def flush(self):
        """
        Currently not needed for UInput? But is a part of the AbstractSysInterface definition
        """
        pass


    def __eventLoop(self):
        while True:
            method, args = self.queue.get()

            if method is None and args is None:
                break
            elif method is not None and args is None:
                logger.debug("__eventLoop: Got method {} with None arguments!".format(method))
            try:
                method(*args)
            except Exception as e:
                logger.exception("Error in UInput event loop thread: {}".format(e))

            self.queue.task_done()


    def grab_hotkey(self, item):
        pass


    def ungrab_hotkey(self, item):
        pass


    @queue_method(queue)
    def grab_keyboard(self, ):
        #TODO: something weird is happening with grab/ungrab
        #self.keyboard.grab()

        self.sending = True

        pass

    @queue_method(queue)
    def ungrab_keyboard(self, ):
        #TODO: need to implement this
        pass
        self.sending = False
        #self.keyboard.ungrab()

    def handle_mouseclick(self, clickEvent):
        self.mediator.handle_mouse_click(clickEvent)

    def on_keys_changed(self, ):
        raise NotImplementedError

    @queue_method(queue)
    def send_modified_key(self, key, modifiers):
        """
        modifiers are expected to be autokey style
        """
        from evdev import ecodes as e # not sure why this is needed here? Decorator maybe doing something weird?
        logger.debug(f"Send modified key: {key}, Modifiers: {modifiers}")
        evdev_keycode, shifted = self.translate_to_evdev(key)
        evdev_key = e.keys[evdev_keycode]


        try:
            # down mods
            for mod in modifiers:
                #convert to KEY_ modifier
                evdev_mod_key = self.autokey_map[mod]
                self.ui.write(e.EV_MSC, e.MSC_SCAN, self.inv_map[evdev_mod_key])
                self.ui.write(e.EV_KEY, self.inv_map[evdev_mod_key], 1)
                self.syn_raw()
            # send key up
            self.ui.write(e.EV_MSC, e.MSC_SCAN, self.inv_map[evdev_key])
            self.ui.write(e.EV_KEY, self.inv_map[evdev_key], 1)
            self.syn_raw()

            # send key down
            self.ui.write(e.EV_MSC, e.MSC_SCAN, self.inv_map[evdev_key])
            self.ui.write(e.EV_KEY, self.inv_map[evdev_key], 0)
            self.syn_raw()


            # up mods
            for mod in modifiers:
                #convert to KEY_ modifier
                evdev_mod_key = self.autokey_map[mod]
                self.ui.write(e.EV_MSC, e.MSC_SCAN, self.inv_map[evdev_mod_key])
                self.ui.write(e.EV_KEY, self.inv_map[evdev_mod_key], 0)
                self.syn_raw()

            pass
        except Exception as e:
            logger.warning("Error sending modified key %r %r: %s", modifiers, key, str(e))


    def cancel(self):
        logger.debug("UInputInterface: Try to exit event thread.")
        self.queue.put_nowait((None, None))
        logger.debug("UInputInterface: Event thread exit marker enqueued.")
        self.shutdown = True
        logger.debug("UInputInterface: Shutdown flag set.")

        self.udev_observer.stop()
        logger.debug('UinputInterface: UDEV MonitorObserver stopped')

        self.listenerThread.join()
        self.eventThread.join()

        self.join()


    def fake_keydown(self, key):
        """
        No such thing as "fake keydown" in UInput. This is passing through to press_key.
        """
        self.press_key(key)

    def fake_keypress(self, key):
        """
        No such thing as "fake keypress" in UInput. This is passing through to send_key.
        """
        #self.press_key(key)
        self.send_key(key)

    def fake_keyup(self, key):
        """
        No such thing as "fake keyup" in UInput. This is passing through to release_key.
        """
        self.release_key(key)

    def get_devices(self):
        return [evdev.InputDevice(path) for path in evdev.list_devices()]

    def grab_device(self, devices, descriptor):
        #determine if descriptor is a path or a name
        return_device = None
        if len(descriptor) <= 2: #assume that people don't have more than 99 input devices
            descriptor = "/dev/input/event"+descriptor
        if "/dev/" in descriptor: #assume function was passed a path
            for device in devices:
                if descriptor==device.path:
                    device.close()
                    return_device = evdev.InputDevice(device.path)
                else:
                    device.close()
        else: #assume that function was passed a plain text name
            for device in devices:
                if descriptor==device.name:
                    device.close()
                    return_device = evdev.InputDevice(device.path)
                else:
                    device.close()

        return return_device


    def translate_to_evdev(self, key):
        """
        Takes an input and tries to convert it to a evdev key code, primarily for internal use
        Determination of type is based primarily on the key type in order;
        if key is type str and the first 4 letters have "KEY_" we assume it is an evdev keycode and return from the inverted mapping of the ecodes.keys
        elif the key is type int we will assume if is a raw evdev value and return it
        elif len(key) == 1, assume that this is an ascii char, check if "KEY_"+key exists in any of the character maps and process accordingly
        return (0, false)
        """
        #TODO this could probably do with an optimization pass
        if type(key)==str and "KEY_" in key[:4]: #if it is a "KEY_A" type value return evdev int from map
            # print("Type str")
            return self.inv_map[key], False
        elif type(key)==list and "BTN_" in key[0][:4]:
            return self.inv_btn_map[key[0]], False
        elif type(key)==str and "BTN_" in key[:4]:
            return self.inv_btn_map[key], False
        elif type(key)==Button:
            return self.btn_map[key]
        elif type(key)==int: #if it is type int it should be a evdev raw value
            # print("Type int")
            return key, False
        elif len(key)==1:
            #print("Type single char", key)
            evdev_key = "KEY_"+key.upper()
            if key in self.shifted_chars:
                return self.inv_map[self.shifted_chars[key]], True
            elif key in self.char_map:
                return self.inv_map[self.char_map[key]], False
            elif evdev_key in self.inv_map:
                return self.inv_map[evdev_key], key.isupper()
            elif evdev_key in self.char_map:
                return self.inv_map[self.char_map[evdev_key]], key.isupper()
        elif type(key)==str and key in self.autokey_map:
            # print("Type <autokey>", key)
            return self.inv_map[self.autokey_map[key]], False
        return (0, False)

    def initialise(self):
        pass

    def run(self):
        pass

    def __processEvent(self):
        pass

    def lookup_string(self, keyCode, shifted, num_lock, altGrid):
        """

        """
        logger.debug("lookup_string: keyCode:{}, Translated:{}, Shifted: {}".format(keyCode, self.translate_to_evdev(keyCode[0]), shifted))

        #if not shifted and not num_lock and not altGrid:
        #TODO handle special keys like backslash etc.
        code, shifted_ = self.translate_to_evdev(keyCode[0])
        evdev_name = e.keys[code]
        # for mouse buttons this returns a list like ['BTN_LEFT', 'BTN_MOUSE']
        if type(evdev_name) is list:
            evdev_name = evdev_name[0]
        # modifiers
        if evdev_name in self.uinput_modifiers_to_ak_map:
            logger.debug("Modifier: {}".format(evdev_name))
            return self.uinput_modifiers_to_ak_map[evdev_name]
        # "keys" like f12 ESC etc.
        if evdev_name in self.uinput_keys_to_ak_map:
            logger.debug("Key: {}".format(evdev_name))
            return self.uinput_keys_to_ak_map[evdev_name]
        character = evdev_name.replace("KEY_", "")
        if character.lower() in self.translation_map:
            character = self.translation_map[character.lower()]
        if shifted:
            return character.upper()
        else:
            return character.lower()
        #return self.translate_to_evdev(keyCode[0])

        #return e.keys[self.translate_to_evdev(keyCode)[0]]
