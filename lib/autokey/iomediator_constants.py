import re
X_RECORD_INTERFACE = "XRecord"
KEY_SPLIT_RE = re.compile("(<[^<>]+>\+?)")

from .iomediator_Key import Key
MODIFIERS = [Key.CONTROL, Key.ALT, Key.ALT_GR, Key.SHIFT, Key.SUPER, Key.HYPER, Key.META, Key.CAPSLOCK, Key.NUMLOCK]
HELD_MODIFIERS = [Key.CONTROL, Key.ALT, Key.SUPER, Key.SHIFT, Key.HYPER, Key.META]
