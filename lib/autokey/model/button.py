# Key codes enumeration
import enum

@enum.unique
class Button(int, enum.Enum):
    #TODO find more verbose link to explanation of buttons
    """
    Enum of Mouse buttons recognized by the X11 server (1-10)

    - ``LEFT = 1`` - left mouse button
    - ``MIDDLE = 2`` - middle or scrollwheel
    - ``RIGHT = 3`` - right mouse button
    - ``SCROLL_UP = 4`` - scroll up
    - ``SCROLL_DOWN = 5`` - scroll down
    - ``SCROLL_LEFT = 6`` - scroll left
    - ``SCROLL_RIGHT = 7`` - scroll right
    - ``BACKWARD = 8`` - backward button
    - ``FORWARD = 9`` - forward button
    - ``BUTTON10 = 10`` - "button10"

    """
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

