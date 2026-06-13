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
from ctypes import c_int, c_uint32, c_char_p, POINTER, byref, c_void_p
from enum import IntEnum
from typing import Optional, List, Tuple

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
            '/usr/lib/libei.so.1',
            '/usr/local/lib/libei.so.1',
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


class WaylandInterface:
    """Wayland backend for input injection via libei."""
    
    def __init__(self):
        self.context = None
        self.keyboard = None
        self._initialized = False
    
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
    
    def type_string(self, text: str) -> bool:
        """Type a string of text."""
        if not self._initialized:
            return False
        
        # Simple implementation: type each character
        for char in text:
            keycode = self._char_to_keycode(char)
            if keycode:
                self.key_press(keycode)
                time.sleep(0.001)
                self.key_release(keycode)
                time.sleep(0.001)
        
        return True
    
    def _char_to_keycode(self, char: str) -> int:
        """Convert character to keycode (simplified)."""
        return ord(char)


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
    
    from .interface import XRecordInterface
    return XRecordInterface()


# Keymap for common keys (simplified mapping)
KEYMAP = {
    'a': 30, 'b': 48, 'c': 46, 'd': 40, 'e': 24, 'f': 41, 'g': 42,
    'h': 43, 'i': 23, 'j': 44, 'k': 45, 'l': 26, 'm': 53, 'n': 54,
    'o': 25, 'p': 16, 'q': 20, 'r': 27, 's': 31, 't': 28, 'u': 29,
    'v': 55, 'w': 17, 'x': 50, 'y': 21, 'z': 47,
    'A': 30 | 0x40, 'B': 48 | 0x40, 'C': 46 | 0x40,
    '1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 9, '9': 10, '0': 11,
    ' ': 57,
}