# Key codes enumeration
import enum

@enum.unique
class Button(int, enum.Enum):
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3
    SCROLL_UP = 4
    SCROLL_DOWN = 5
    SCROLL_LEFT = 6
    SCROLL_RIGHT = 7
    BACKWARD = 8
    FORWARD = 9
    BUTTON10 = 10

