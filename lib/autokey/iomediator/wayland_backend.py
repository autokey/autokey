# -*- coding: utf-8 -*-
# Wayland Backend for AutoKey
# Provides input injection for Wayland compositors using libei
# 
# Copyright (C) 2024 Ghost Development
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Wayland backend implementation using libei for input injection.
This module provides an alternative to X11 when running under Wayland.
"""

import os
import sys
import time
import ctypes
from ctypes import c_int, c_uint32, c_char_p, POINTER, byref, c_void_p, c_size_t
from enum import IntEnum
from typing import Optional, List, Tuple, Dict, Any

import logging
logger = logging.getLogger(__name__)


class EeiProtocol(IntEnum):
    """libei protocol types."""
    KEYBOARD = 0
    POINTER = 1
    TEXT = 2


class EeiKey(IntEnum):
    """Keyboard event types."""
    PRESS = 0
    RELEASE = 1


class LibeiLoader:
    """Dynamic loader for libei shared library."""
    
    def __init__(self):
        self.lib = None
        self._load_library()
    
    def _load_library(self):
        lib_names = [
            'libei.so.1',
            'libei.so',
            '/usr/lib/x86_64-linux-gnu/libei.so.1',
            '/usr/lib/x86_64-linux-gnu/libei.so',
            '/usr/lib/libei.so.1',
            '/usr/lib/libei.so',
            '/usr/local/lib/libei.so.1',
            '/usr/local/lib/libei.so',
        ]
        
        for lib_name in lib_names:
            try:
                if os.path.exists(lib_name) or lib_name.startswith('libei'):
                    self.lib = ctypes.CDLL(lib_name)
                    logger.info(f"Loaded libei from {lib_name}")
                    self._setup_functions()
                    return
            except OSError:
                continue
        
        raise ImportError("libei not found. Install with: apt install libei-dev")
    
    def _setup_functions(self):
        self.lib.eei_context_new.restype = c_void_p
        self.lib.eei_context_new.argtypes = []
        
        self.lib.eei_context_connect.restype = c_int
        self.lib.eei_context_connect.argtypes = [c_void_p, c_char_p]
        
        self.lib.eei_keyboard_new.restype = c_void_p
        self.lib.eei_keyboard_new.argtypes = [c_void_p]
        
        self.lib.eei_keyboard_commit.restype = c_int
        self.lib.eei_keyboard_commit.argtypes = [c_void_p]
        
        self.lib.eei_keyboard_key.restype = c_int
        self.lib.eei_keyboard_key.argtypes = [c_void_p, c_int, c_int]
        
        self.lib.eei_keyboard_release.restype = c_int
        self.lib.eei_keyboard_release.argtypes = [c_void_p]
        
        self.lib.eei_device_info_new.restype = c_void_p
        self.lib.eei_device_info_new.argtypes = []
        
        self.lib.eei_device_info_get_id.restype = c_char_p
        self.lib.eei_device_info_get_id.argtypes = [c_void_p]
        
        self.lib.eei_device_info_free.restype = None
        self.lib.eei_device_info_free.argtypes = [c_void_p]


KEYMAP = {
    'a': 30, 'b': 48, 'c': 46, 'd': 40, 'e': 24, 'f': 41, 'g': 42,
    'h': 43, 'i': 23, 'j': 44, 'k': 45, 'l': 26, 'm': 53, 'n': 54,
    'o': 25, 'p': 16, 'q': 20, 'r': 27, 's': 31, 't': 28, 'u': 29,
    'v': 55, 'w': 17, 'x': 50, 'y': 21, 'z': 47,
    'A': 30 | 0x40, 'B': 48 | 0x40, 'C': 46 | 0x40,
    '1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 9, '9': 10, '0': 11,
    ' ': 57,
    '\n': 40, '\r': 40, '\t': 15,
    '`': 41, '-': 12, '=': 13, '[': 26, ']': 27, '\\': 43,
    ';': 39, "'": 40, ',': 51, '.': 52, '/': 56,
}

MODIFIER_KEYMAP = {
    'ctrl': 91, 'Ctrl': 91, '<ctrl>': 91,
    'alt': 92, 'Alt': 92, '<alt>': 92,
    'shift': 93, 'Shift': 93, '<shift>': 93,
    'super': 94, 'Super': 94, '<super>': 94,
    'meta': 95, 'Meta': 95, '<meta>': 95,
}


class WaylandInterface:
    """Wayland backend for input injection via libei."""
    
    def __init__(self):
        self.context = None
        self.keyboard = None
        self._lib: Optional[LibeiLoader] = None
        self._initialized = False
        self._focused = False
    
    def initialise(self) -> bool:
        """Initialize Wayland backend via libei."""
        return self.initialize()
    
    def initialize(self) -> bool:
        """Initialize Wayland backend via libei."""
        try:
            self._lib = LibeiLoader()
            self.context = self._lib.lib.eei_context_new()
            
            display = os.environ.get('WAYLAND_DISPLAY', 'wayland-0')
            result = self._lib.lib.eei_context_connect(self.context, display.encode())
            
            if result != 0:
                logger.error(f"Failed to connect to Wayland display: {result}")
                return False
            
            self.keyboard = self._lib.lib.eei_keyboard_new(self.context)
            if not self.keyboard:
                logger.error("Failed to create keyboard object")
                return False
            
            self._initialized = True
            logger.info("Wayland interface initialized via libei")
            return True
            
        except Exception as e:
            logger.exception(f"Wayland initialization failed: {e}")
            return False
    
    def start(self):
        """Start the interface - commit the keyboard."""
        if self._initialized and self.keyboard:
            self._lib.lib.eei_keyboard_commit(self.keyboard)
    
    def cancel(self):
        """Cancel/shutdown the interface."""
        if self.keyboard:
            self._lib.lib.eei_keyboard_release(self.keyboard)
        self._initialized = False
    
    def _keycode_for_key(self, key: str) -> int:
        """Convert key name to keycode."""
        if key in KEYMAP:
            return KEYMAP[key]
        if key.lower() in KEYMAP:
            return KEYMAP[key.lower()]
        if key in MODIFIER_KEYMAP:
            return MODIFIER_KEYMAP[key]
        return ord(key) if len(key) == 1 else 0
    
    def lookup_string(self, key_code: int, shifted: bool, num_lock: bool, alt_gr: bool) -> str:
        """Lookup string for a key code - simplified implementation."""
        for char, code in KEYMAP.items():
            if code == key_code:
                if shifted and char.isalpha():
                    return char.upper()
                return char
        return chr(key_code) if key_code < 256 else ''
    
    def grab_keyboard(self):
        """Grab keyboard - libei handles this implicitly."""
        pass
    
    def ungrab_keyboard(self):
        """Ungrab keyboard."""
        pass
    
    def send_modified_key(self, key: str, modifiers: List[str]):
        """Send a key with modifiers held."""
        mod_codes = []
        for mod in modifiers:
            code = self._keycode_for_key(mod)
            if code:
                mod_codes.append(code)
                self.key_press(code)
        
        self.send_key(key)
        
        for code in reversed(mod_codes):
            self.key_release(code)
    
    def send_key(self, key_name: str):
        """Send a single key press and release."""
        keycode = self._keycode_for_key(key_name)
        if keycode:
            self.key_press(keycode)
            time.sleep(0.005)
            self.key_release(keycode)
    
    def send_string(self, text: str):
        """Send a string of text."""
        for char in text:
            keycode = self._keycode_for_key(char)
            if keycode:
                self.key_press(keycode)
                time.sleep(0.002)
                self.key_release(keycode)
                time.sleep(0.002)
    
    def fake_keydown(self, key_name: str):
        """Generate key down event."""
        keycode = self._keycode_for_key(key_name)
        if keycode:
            self.key_press(keycode)
    
    def fake_keyup(self, key_name: str):
        """Generate key up event."""
        keycode = self._keycode_for_key(key_name)
        if keycode:
            self.key_release(keycode)
    
    def fake_keypress(self, key_name: str):
        """Generate a full keypress."""
        self.send_key(key_name)
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position - simplified placeholder."""
        return (0, 0)
    
    def send_mouse_click(self, root_x: int, root_y: int, button: int, double: bool):
        """Send mouse click - not implemented in libei yet."""
        logger.warning("Mouse click not implemented for libei backend")
    
    def flush(self):
        """Flush pending events."""
        if self._initialized and self.keyboard:
            self._lib.lib.eei_keyboard_commit(self.keyboard)
    
    def key_press(self, keycode: int) -> bool:
        """Inject a key press event."""
        if not self._initialized:
            return False
        try:
            self._lib.lib.eei_keyboard_key(self.keyboard, keycode, int(EeiKey.PRESS))
            return True
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False
    
    def key_release(self, keycode: int) -> bool:
        """Inject a key release event."""
        if not self._initialized:
            return False
        try:
            self._lib.lib.eei_keyboard_key(self.keyboard, keycode, int(EeiKey.RELEASE))
            return True
        except Exception as e:
            logger.error(f"Key release failed: {e}")
            return False


def detect_display_server() -> str:
    """Detect current display server."""
    if 'WAYLAND_DISPLAY' in os.environ:
        return 'wayland'
    elif 'DISPLAY' in os.environ:
        return 'x11'
    return 'unknown'


def get_input_interface():
    """Factory function to get appropriate input interface."""
    display = detect_display_server()
    
    if display == 'wayland':
        try:
            interface = WaylandInterface()
            if interface.initialize():
                return interface
        except ImportError:
            pass
        logger.warning("Wayland detected but libei not available, falling back to X11")
    
    from autokey.interface import XRecordInterface
    return XRecordInterface()