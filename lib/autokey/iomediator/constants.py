import re

from .key import Key

X_RECORD_INTERFACE = "XRecord"
KEY_SPLIT_RE = re.compile("(<[^<>]+>\+?)")

MODIFIERS = [Key.CONTROL, Key.ALT, Key.ALT_GR, Key.SHIFT, Key.SUPER, Key.HYPER, Key.META, Key.CAPSLOCK, Key.NUMLOCK]
HELD_MODIFIERS = [Key.CONTROL, Key.ALT, Key.SUPER, Key.SHIFT, Key.HYPER, Key.META]
