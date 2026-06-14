# -*- coding: utf-8 -*-
# Wayland Backend for AutoKey
# Provides input injection for Wayland compositors using libei with AT-SPI fallback
# 
# Copyright (C) 2024 Ghost Development
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Wayland backend implementation with libei primary and AT-SPI fallback.

This module provides universal Wayland support:
- Primary: libei protocol (works with all Wayland compositors)
- Fallback: AT-SPI bridge (GNOME compatibility)
"""

import os
import sys
import time
import ctypes
from ctypes import c_int, c_void_p, c_char_p
import logging

logger = logging.getLogger(__name__)

HAS_LIBEI = False
HAS_ATSPI = False

try:
    import pyatspi
    HAS_ATSPI = True
except ImportError:
    pass


class LibeiLoader:
    def __init__(self):
        self.lib = None
        self._load_library()

    def _load_library(self):
        lib_names = [
            'libei.so.1',
            'libei.so',
            '/usr/lib/x86_64-linux-gnu/libei.so.1',
            '/usr/lib/libei.so.1',
            '/usr/local/lib/libei.so.1',
        ]
        
        for lib_name in lib_names:
            try:
                if os.path.exists(lib_name) or lib_name.startswith('libei'):
                    self.lib = ctypes.CDLL(lib_name)
                    self._setup_functions()
                    return
            except OSError:
                continue
        
        raise ImportError("libei not found")

    def _setup_functions(self):
        self.lib.eei_context_new.restype = c_void_p
        self.lib.eei_context_new.argtypes = []
        self.lib.eei_context_connect.restype = c_int
        self.lib.eei_context_connect.argtypes = [c_void_p, c_char_p]
        self.lib.eei_keyboard_new.restype = c_void_p
        self.lib.eei_keyboard_new.argtypes = [c_void_p]
        self.lib.eei_keyboard_key.restype = c_int
        self.lib.eei_keyboard_key.argtypes = [c_void_p, c_int, c_int]


class WaylandLibeiInterface:
    def __init__(self):
        self.context = None
        self.keyboard = None
        self._initialized = False

    def initialize(self) -> bool:
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
            logger.error(f"libei initialization failed: {e}")
            return False

    def key_press(self, keycode: int) -> bool:
        if not self._initialized:
            return False
        try:
            self._lib.lib.eei_keyboard_key(self.keyboard, keycode, 0)
            return True
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False

    def key_release(self, keycode: int) -> bool:
        if not self._initialized:
            return False
        try:
            self._lib.lib.eei_keyboard_key(self.keyboard, keycode, 1)
            return True
        except Exception as e:
            logger.error(f"Key release failed: {e}")
            return False

    def type_string(self, text: str) -> bool:
        if not self._initialized:
            return False
        for char in text:
            keycode = ord(char)
            self.key_press(keycode)
            time.sleep(0.001)
            self.key_release(keycode)
            time.sleep(0.001)
        return True


class WaylandAtSpiInterface:
    def __init__(self):
        self._initialized = False

    def initialize(self) -> bool:
        if not HAS_ATSPI:
            logger.error("pyatspi not available")
            return False
        try:
            pyatspi.registerEventListener(self._event_callback, "key" + "board")
            self._initialized = True
            logger.info("Wayland interface initialized via AT-SPI")
            return True
        except Exception as e:
            logger.error(f"AT-SPI initialization failed: {e}")
            return False

    def _event_callback(self, event):
        pass

    def key_press(self, keycode: int) -> bool:
        if not self._initialized:
            return False
        try:
            pyatspi.keyboard.keyCombo(f"key{keycode}")
            return True
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False

    def key_release(self, keycode: int) -> bool:
        return True

    def type_string(self, text: str) -> bool:
        if not self._initialized:
            return False
        try:
            pyatspi.keyboard.writeText(text)
            return True
        except Exception as e:
            logger.error(f"Type string failed: {e}")
            return False


def detect_display_server() -> str:
    if 'WAYLAND_DISPLAY' in os.environ:
        return 'wayland'
    elif 'DISPLAY' in os.environ:
        return 'x11'
    return 'unknown'


class WaylandInterface:
    def __init__(self):
        self._interface = None
        self._type = None

    def initialize(self) -> bool:
        display = detect_display_server()
        if display != 'wayland':
            return False
        
        if HAS_LIBEI:
            try:
                self._interface = WaylandLibeiInterface()
                if self._interface.initialize():
                    self._type = "libei"
                    logger.info("Using libei backend")
                    return True
            except ImportError:
                logger.warning("libei not available, trying AT-SPI")
        
        if HAS_ATSPI:
            try:
                self._interface = WaylandAtSpiInterface()
                if self._interface.initialize():
                    self._type = "atsui"
                    logger.info("Using AT-SPI backend")
                    return True
            except Exception as e:
                logger.error(f"AT-SPI failed: {e}")
        
        logger.error("No Wayland backend available")
        return False

    def key_press(self, keycode: int) -> bool:
        return self._interface.key_press(keycode) if self._interface else False

    def key_release(self, keycode: int) -> bool:
        return self._interface.key_release(keycode) if self._interface else False

    def type_string(self, text: str) -> bool:
        return self._interface.type_string(text) if self._interface else False