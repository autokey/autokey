# Key codes enumeration
import enum
import re

# Matches the special <code[number]> syntax, like <code86> for non-printable or unknown keys.
_code_point_re = re.compile(r"<code(0|[1-9][0-9]*)>", re.UNICODE)


@enum.unique
class Key(str, enum.Enum):
    """
    An enumeration of the "special" keys Autokey is able to listen for/send
    """
    LEFT = "<left>"
    """LEFT arrow key"""
    RIGHT = "<right>"
    """RIGHT arrow key"""
    UP = "<up>"
    """UP arrow key """
    DOWN = "<down>"
    """DOWN arrow key """
    BACKSPACE = "<backspace>"
    """Backspace key"""
    TAB = "<tab>"
    """Tab key"""
    ENTER = "<enter>"
    """Enter key"""
    SCROLL_LOCK = "<scroll_lock>"
    """Scroll lock key"""
    PRINT_SCREEN = "<print_screen>"
    """Print screen key"""
    PAUSE = "<pause>"
    """Pause key"""
    MENU = "<menu>"
    """Menu key"""
    
    # Modifier keys
    CONTROL = "<ctrl>"
    """CONTROL key"""
    ALT = "<alt>"
    """ALT key"""
    ALT_GR = "<alt_gr>"
    """ALT_GR key"""
    SHIFT = "<shift>"
    """SHIFT key"""
    SUPER = "<super>"
    """SUPER key"""
    HYPER = "<hyper>"
    """HYPER key"""
    CAPSLOCK = "<capslock>"
    """CAPSLOCK key"""
    NUMLOCK = "<numlock>"
    """NUMLOCK key"""
    META = "<meta>"
    """META key"""
    
    F1 = "<f1>"
    """F1 key"""
    F2 = "<f2>"
    """F2 key"""
    F3 = "<f3>"
    """F3 key"""
    F4 = "<f4>"
    """F4 key"""
    F5 = "<f5>"
    """F5 key"""
    F6 = "<f6>"
    """F6 key"""
    F7 = "<f7>"
    """F7 key"""
    F8 = "<f8>"
    """F8 key"""
    F9 = "<f9>"
    """F9 key"""
    F10 = "<f10>"
    """F10 key"""
    F11 = "<f11>"
    """F11 key"""
    F12 = "<f12>"
    """F12 key"""
    F13 = "<f13>"
    """F13 key"""
    F14 = "<f14>"
    """F14 key"""
    F15 = "<f15>"
    """F15 key"""
    F16 = "<f16>"
    """F16 key"""
    F17 = "<f17>"
    """F17 key"""
    F18 = "<f18>"
    """F18 key"""
    F19 = "<f19>"
    """F19 key"""
    F20 = "<f20>"
    """F20 key"""
    F21 = "<f21>"
    """F21 key"""
    F22 = "<f22>"
    """F22 key"""
    F23 = "<f23>"
    """F23 key"""
    F24 = "<f24>"
    """F24 key"""
    F25 = "<f25>"
    """F25 key"""
    F26 = "<f26>"
    """F26 key"""
    F27 = "<f27>"
    """F27 key"""
    F28 = "<f28>"
    """F28 key"""
    F29 = "<f29>"
    """F29 key"""
    F30 = "<f30>"
    """F30 key"""
    F31 = "<f31>"
    """F31 key"""
    F32 = "<f32>"
    """F32 key"""
    F33 = "<f33>"
    """F33 key"""
    F34 = "<f34>"
    """F34 key"""
    F35 = "<f35>"
    """F35 key"""
    

    # Other
    ESCAPE = "<escape>"
    """ESCAPE key"""
    INSERT = "<insert>"
    """INSERT key"""
    DELETE = "<delete>"
    """DELETE key"""
    HOME = "<home>"
    """HOME key"""
    END = "<end>"
    """END key"""
    PAGE_UP = "<page_up>"
    """PAGE_UP key"""
    PAGE_DOWN = "<page_down>"
    """PAGE_DOWN key"""


    # Numpad
    NP_INSERT = "<np_insert>"
    """Number pad insert key"""
    NP_DELETE = "<np_delete>"
    """Number pad delete key"""
    NP_HOME = "<np_home>"
    """Number pad home key"""
    NP_END = "<np_end>"
    """Number pad end key"""
    NP_PAGE_UP = "<np_page_up>"
    """Number pad page up key"""
    NP_PAGE_DOWN = "<np_page_down>"
    """Number pad page down key"""
    NP_LEFT = "<np_left>"
    """Number pad left key"""
    NP_RIGHT = "<np_right>"
    """Number pad right key"""
    NP_UP = "<np_up>"
    """Number pad up key"""
    NP_DOWN = "<np_down>"
    """Number pad down key"""
    NP_DIVIDE = "<np_divide>"
    """Number pad divide key"""
    NP_MULTIPLY = "<np_multiply>"
    """Number pad multiply key"""
    NP_ADD = "<np_add>"
    """Number pad add key"""
    NP_SUBTRACT = "<np_subtract>"
    """Number pad subtract key"""
    NP_5 = "<np_5>"
    """Number pad 5 key"""


    @classmethod
    def is_key(cls, key_string: str) -> bool:
        """
        Returns if a string represents a key.
        """
        # Key strings must be treated as case insensitive - always convert to lowercase
        # before doing any comparisons
        lowered_key_string = key_string.lower()
        try:
            cls(lowered_key_string)
        except ValueError:
            return _code_point_re.fullmatch(lowered_key_string) is not None
        else:
            return True


NAVIGATION_KEYS = [Key.LEFT, Key.RIGHT, Key.UP, Key.DOWN, Key.BACKSPACE, Key.HOME, Key.END, Key.PAGE_UP, Key.PAGE_DOWN]
# All known modifier keys. This is used to determine if a key is a modifier. Used by the Configuration manager
# to verify that only modifier keys are placed in the disabled modifiers list.
_ALL_MODIFIERS_ = (
    Key.CONTROL, Key.ALT, Key.ALT_GR, Key.SHIFT, Key.SUPER, Key.HYPER, Key.CAPSLOCK, Key.NUMLOCK, Key.META
)

# Used to identify special keys in texts. Also include <codeXX> literals as defined in the _code_point_re.
KEY_FIND_RE = re.compile("|".join(("|".join(Key), _code_point_re.pattern)), re.UNICODE)
KEY_SPLIT_RE = re.compile("(<[^<>]+>\+?)")
MODIFIERS = [Key.CONTROL, Key.ALT, Key.ALT_GR, Key.SHIFT, Key.SUPER, Key.HYPER, Key.META, Key.CAPSLOCK, Key.NUMLOCK]
HELD_MODIFIERS = [Key.CONTROL, Key.ALT_GR, Key.ALT, Key.SUPER, Key.SHIFT, Key.HYPER, Key.META
]
