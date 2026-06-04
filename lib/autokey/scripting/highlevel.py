"""
Highlevel scripting API, requires xautomation to be installed
"""

import time
import os
import subprocess
import tempfile
import magic
import struct


class PatternNotFound(Exception):
    """Exception raised by functions"""
    pass

# numeric representation of the mouse buttons. For use in visgrep.
LEFT = 1
"""Left mouse button"""
MIDDLE = 2
"""Middle mouse button"""
RIGHT = 3
"""Right mouse button"""


def visgrep(scr: str, pat: str, tolerance: int = 0) -> int:
    """
    Usage: C{visgrep(scr: str, pat: str, tolerance: int = 0) -> int}

    Visual grep of scr for pattern pat.

    Requires xautomation (http://hoopajoo.net/projects/xautomation.html).

    Usage: C{visgrep("screen.png", "pat.png")}

    

    :param scr: path of PNG image to be grepped.
    :param pat: path of pattern image (PNG) to look for in scr.
    :param tolerance: An integer ≥ 0 to specify the level of tolerance for 'fuzzy' matches.
    :raise ValueError: Raised if tolerance is negative or not convertable to int
    :raise PatternNotFound: Raised if C{pat} not found.
    :raise FileNotFoundError: Raised if either file is not found
    :returns: Coordinates of the topleft point of the match, if any. Raises L{PatternNotFound} exception otherwise.
    """
    tol = int(tolerance)
    if tol < 0:
        raise ValueError("tolerance must be ≥ 0.")
    with open(scr), open(pat):
        pass
    with tempfile.NamedTemporaryFile() as f:
        subprocess.call(['png2pat', pat], stdout=f)
        # don't use check_call, some versions (1.05) have a missing return statement in png2pat.c so the exit status ≠ 0
        f.flush()
        os.fsync(f.fileno())
        vg = subprocess.Popen(['visgrep', '-t' + str(tol), scr, f.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = vg.communicate()
    coord_str = out[0].decode().split(' ')[0].split(',')
    try:
        coord = [int(coord_str[0]), int(coord_str[1])]
    except (ValueError, IndexError) as e:
        raise PatternNotFound(str([x.decode() for x in out]) + '\n\t' + repr(e))
    return coord


def get_png_dim(filepath: str) -> int:
    """
    Usage: C{get_png_dim(filepath:str) -> (int)}

    Finds the dimension of a PNG.
    :param filepath: file path of the PNG.
    :returns: (width, height).
    :raise Exception: Raised if the file is not a png
    """
    with open(filepath, 'rb') as f:
        if not magic.detect_from_fobj(f).mime_type == "image/png":
            raise Exception("not PNG")
        head = f.read(24)
        return struct.unpack('!II', head[16:24])


def mouse_move(x: int, y: int, display: str=''):
    """
    Moves the mouse using xte C{mousemove} from xautomation

    :param x: x location to move the mouse to
    :param y: y location to move the mouse to
    :param display: X display to pass to C{xte}
    """
    subprocess.call(['xte', '-x', display, "mousemove {} {}".format(int(x), int(y))])


def mouse_rmove(x: int, y: int, display: str=''):
    """
    Moves the mouse using xte C{mousermove} command from xautomation

    :param x: x location to move the mouse to
    :param y: y location to move the mouse to
    :param display: X display to pass to C{xte}
    """
    subprocess.call(['xte', '-x', display, "mousermove {} {}".format(int(x), int(y))])


def mouse_click(button: int, display: str=''):
    """
    Clicks the mouse in the current location using xte C{mouseclick} from xautomation

    :param button: Which button signal to send from the mouse
    :param display: X display to pass to C{xte}
    """
    subprocess.call(['xte', '-x', display, "mouseclick {}".format(int(button))])


def mouse_pos():
    """
    Returns the current location of the mouse.

    :returns: Returns the mouse location in a C{list}
    """
    tmp = subprocess.check_output("xmousepos").decode().split()
    return list(map(int, tmp))[:2]


def click_on_pat(pat: str, mousebutton: int=1, offset: (float, float)=None, tolerance: int=0, restore_pos: bool=False) -> None:
    """
    Requires C{imagemagick}, C{xautomation}, C{xwd}.

    Click on a pattern at a specified offset (x,y) in percent of the pattern dimension. x is the horizontal distance from the top left corner, y is the vertical distance from the top left corner. By default, the offset is (50,50), which means that the center of the pattern will be clicked at.

    :param pat: path of pattern image (PNG) to click on.
    :param mousebutton: mouse button number used for the click
    :param offset: offset from the top left point of the match. (float,float)
    :param tolerance: An integer ≥ 0 to specify the level of tolerance for 'fuzzy' matches. If negative or not convertible to int, raises ValueError.
    :param restore_pos: return to the initial mouse position after the click.
    :raise PatternNotFound: Raised when the pattern is not found on the screen
    """
    x0, y0 = mouse_pos()
    move_to_pat(pat, offset, tolerance)
    mouse_click(mousebutton)
    if restore_pos:
        mouse_move(x0, y0)


def move_to_pat(pat: str, offset: (float, float)=None, tolerance: int=0) -> None:
    """See L{click_on_pat}"""
    with tempfile.NamedTemporaryFile() as f:
        subprocess.call('''
        xwd -root -silent -display :0 | 
        convert xwd:- png:''' + f.name, shell=True)
        loc = visgrep(f.name, pat, tolerance)
    pat_size = get_png_dim(pat)
    if offset is None:
        x, y = [l + ps//2 for l, ps in zip(loc, pat_size)]
    else:
        x, y = [l + ps*(off/100) for off, l, ps in zip(offset, loc, pat_size)]
    mouse_move(x, y)


def acknowledge_gnome_notification():
    """
    Moves mouse pointer to the bottom center of the screen and clicks on it.
    """
    x0, y0 = mouse_pos()
    mouse_move(10000, 10000)  # TODO: What if the screen is larger? Loop until mouse position does not change anymore?
    x, y = mouse_pos()
    mouse_rmove(-x/2, 0)
    mouse_click(LEFT)
    time.sleep(.2)
    mouse_move(x0, y0)

