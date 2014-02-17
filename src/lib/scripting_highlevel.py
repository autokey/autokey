import os
import subprocess
import tempfile
import imghdr, struct


class PatternNotFound(Exception):
    pass

# numeric representation of the mouse buttons. For use in visgrep.
LEFT = 1
MIDDLE = 2
RIGHT = 3


def visgrep(scr:str, pat:str, tolerance:int = 0) -> (int,int):
    """
    visgrep(scr:str, pat:str, tolerance:int = 0) -> (int,int)
    Visual grep of scr for pattern pat.
    Requires xautomation (http://hoopajoo.net/projects/xautomation.html).
    visgrep("screen.png", "pat.png")
    Exceptions raised: ValueError, PatternNotFound, FileNotFoundError

    :param scr: path of PNG image to be grepped.
    :param pat: path of pattern image (PNG) to look for in scr.
    :param tolerance: An integer ≥ 0 to specify the level of tolerance for 'fuzzy' matches. If negative or not convertible to int, raises ValueError.
    :returns: coordinates of the topleft point of the match, if any. Raises PatternNotFound exception otherwise.
    """
    tol = int(tolerance)
    if tol < 0:
        raise ValueError("tolerance must be ≥ 0.")
    with open(scr), open(pat): pass
    with tempfile.NamedTemporaryFile() as f:
        subprocess.call(['png2pat',pat], stdout=f)
        # don't use check_call, some versions (1.05) have a missing return statement in png2pat.c so the exit status ≠ 0
        f.flush()
        os.fsync(f.fileno())
        vg = subprocess.Popen(['visgrep', '-t' + str(tol), scr, f.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = vg.communicate()
    coord_str =  out[0].decode().split(' ')[0].split(',')
    try:
        coord = [int(coord_str[0]), int(coord_str[1])]
    except (ValueError, IndexError) as e:
        raise PatternNotFound(str([x.decode() for x in out]) + '\n\t' + repr(e))
    return coord

def get_png_dim(filepath:str) -> (int,int):
    '''
    get_png_dim(filepath:str) -> (int,int)
    Finds the dimension of a PNG.
    :param filepath: file path of the PNG.
    :returns: (width, height).
    '''
    if not imghdr.what(filepath)=='png':
        raise Exception("not PNG")
    head = open(filepath, 'rb').read(24)
    return struct.unpack('!II', head[16:24])

def click_on_pat(pat:str, mousebutton:int=1, offset:(float,float)=None, tolerance:int=0, restore_pos:bool = False) -> None:
    """
    Requires imagemagick, xautomation.
    Click on a pattern at a specified offset (b,h) in percent of the patterns dimensions. b is the distance below the top left corner, h is the distance from the top left corner. By default, the offset is (50,50), which means that the center of the pattern will be clicked at.
    Exception PatternNotFound is raised when the pattern is not found on the screen.
    :param pat: path of pattern image (PNG) to click on.
    :param mousebutton: mouse button number used for the click
    :param offset: offset from the top left point of the match. (float,float)
    :param tolerance: An integer ≥ 0 to specify the level of tolerance for 'fuzzy' matches. If negative or not convertible to int, raises ValueError.
    :param restore_pos: return to the initial mouse position after the click.
    """
    with tempfile.NamedTemporaryFile() as f:
        subprocess.call('''
        xwd -root -silent -display :0 | 
        convert xwd:- png:''' + f.name, shell=True)
        loc = visgrep(f.name, pat, tolerance)
    pat_size = get_png_dim(pat)
    if offset is None:
        x, y = [l + ps//2 for l,ps in zip(loc,pat_size)]
    else:
        x, y = [l + ps*(off/100) for off,l,ps in zip(offset,loc,pat_size)]
    x0, y0 = subprocess.check_output("xmousepos").decode().split()[:2]
    subprocess.call('''
xte -x :0 "mousemove {x} {y}"
xte -x :0 "mouseclick {button}"
'''.format(x=int(x),y=int(y), # must be cast to int
           button=mousebutton), shell=True)
    if restore_pos:
        subprocess.call('''xte -x :0 "mousemove {x0} {y0}"'''.format(x0=x0,y0=y0), shell=True)

