from unittest.mock import MagicMock, patch

import pytest
from hamcrest import *

from autokey.scripting import Window

def create_window():
    win = Window(MagicMock())
    return win

def test_window_wait_for_focus() -> Window:
    #TODO tests
    pass

def test_window_wait_for_exist():
    pass

def test_window_activate():
    pass

def test_window_close():
    pass

def test_window_resize_move():
    pass

def test_window_move_to_desktop():
    pass

def test_window_switch_desktop():
    pass

def test_window_set_property():
    pass

def test_window_get_active_geometry():
    pass

def test_window_get_active_title():
    pass

def test_window_get_active_class():
    pass

       #Monitors: 2
        # 0: +*HDMI-0 1920/521x1080/293+0+0  HDMI-0
        # 1: +DVI-D-0 1440/408x900/255+1920+0  DVI-D-0
xrandr_raw_double = """Monitors: 2
 0: +*HDMI-0 1920/521x1080/293+0+0  HDMI-0
 1: +DVI-D-0 1440/408x900/255+1920+0  DVI-D-0"""
xrandr_raw_single = """Monitors: 1
 0: +*DVI-D-0 1440/408x900/255+0+0  DVI-D-0"""

@pytest.mark.parametrize("title, xrandr_raw_output, matchClass", [
    (None, (0, xrandr_raw_single), False), #single monitor
    (None, (0, xrandr_raw_double), False), #double monitor
    (":ACTIVE:", (0, xrandr_raw_double), False),
    ("AutoKey", (0, xrandr_raw_double), False),
])
def test_window_center_window(title, xrandr_raw_output, matchClass):
    window = create_window()
    xrandr = MagicMock(return_value = xrandr_raw_output)
    with patch("autokey.scripting.window.Window.set_property") as set_prop:
        with patch("autokey.scripting.window.Window.resize_move") as resize_move:
            with patch("autokey.scripting.window.Window._run_xrandr", xrandr) as randr:
                window.center_window(title)
                # called with only checks the last time the method was called
                # set_prop.assert_called_with(title, "remove", "maximized_vert", matchClass=matchClass)
                # resize_move.assert_called_with(title, , , , )
                set_prop.assert_called_with(title, "remove", "maximized_horz", matchClass=matchClass)

@pytest.mark.parametrize("wmctrl_output, func_output", [
    (
        (0, """0x02000007  0 samdesktop Desktop
0x0200000f  0 samdesktop nemo-desktop"""),
    [
        ("0x02000007","0","samdesktop", "Desktop"),
        ("0x0200000f", "0" ,"samdesktop", "nemo-desktop")
    ]
)])
def test_window_get_window_list(wmctrl_output, func_output):
    print(wmctrl_output)
    #Example output of
    #$ wmctrl -l
    #0x02000007  0 samdesktop Desktop
    #0x0200000f  0 samdesktop nemo-desktop
    #0x02a00003  0 samdesktop Add more functions to window API by sebastiansam55 · Pull Request #471 · autokey/autokey — Mozilla Firefox
    #0x02a0004d  1 samdesktop (2698) Best of the Worst: Wheel of the Worst #20 - YouTube — Mozilla Firefox
    #0x04000007  1 samdesktop Bluetooth Devices
    #0x04400004  0 samdesktop tmux /home/sam
    #0x06600004  0 samdesktop python3 /home/sam/git/ak-fork/lib
    #0x0700000a  0 samdesktop Downloads
    #0x07c00003  0 samdesktop Find Results (autokey)
    #0x07800004  0 samdesktop wmctrl /home/sam
    #0x08400014  0 samdesktop ak-fork - [~/git/ak-fork]
    #0x07200007  0 samdesktop AutoKey
    ########
    # Each line consists of 4 items in order
    #1. hexid - Hex identifier of the window used by other methods
    #2. desktop - Which "desktop" (currently called workspaces in Ubuntu 20.04)
    #3. hostname - Hostname of the computer the window is located on (?)
    #   Not sure exactly what charaters are allowed in the hostname
    #4. title - Title of the window
    window = create_window()
    wmctrl = MagicMock(return_value = wmctrl_output)
    with patch("autokey.scripting.window.Window._run_wmctrl", wmctrl):
        assert func_output == window.get_window_list()


@pytest.mark.parametrize("title, func_output, get_window_list_output",[
    ("AutoKey", "0x07200007", [("0x07200007", "0", "samdesktop", "AutoKey"),("0x02000007", "0", "samdesktop", "Desktop")]),
])
def test_window_get_window_hex(title, func_output, get_window_list_output):
    #TODO there is probably some way to not have to write this at the top of every function
    window = create_window()
    get_window = MagicMock(return_value = get_window_list_output)
    with patch("autokey.scripting.window.Window.get_window_list", get_window):
        assert func_output == window.get_window_hex(title)
        # get_window.assert_called_with()


@pytest.mark.parametrize("hexid, wmctrl_output, expected", [
    ("0x02a0004d", (0, """0x02a00003  0 0    0    1920 1056 samdesktop Add more functions to window API by sebastiansam55 · Pull Request #471 · autokey/autokey — Mozilla Firefox
0x02a0004d  1 574  301  720  583  samdesktop (2702) Best of the Worst: Wheel of the Worst #20 - YouTube — Mozilla Firefox
0x04000007  1 2371 319  578  350  samdesktop Bluetooth Devices
0x04400004  0 3840 0    1440 876  samdesktop tmux /home/sam"""), [574,301,720,583]),
])
def test_window_get_window_geom(hexid, wmctrl_output, expected):
    #Example Output:
    #$ wmctrl -lG
    #0x02a00003  0 0    0    1920 1056 samdesktop Add more functions to window API by sebastiansam55 · Pull Request #471 · autokey/autokey — Mozilla Firefox
    #0x02a0004d  1 574  301  720  583  samdesktop (2702) Best of the Worst: Wheel of the Worst #20 - YouTube — Mozilla Firefox
    #0x04000007  1 2371 319  578  350  samdesktop Bluetooth Devices
    #0x04400004  0 3840 0    1440 876  samdesktop tmux /home/sam
    #0x06600004  0 1023 187  800  600  samdesktop python3 /home/sam/git/ak-fork/lib
    #0x0700000a  0 76   142  1288 550  samdesktop Downloads
    #0x07800004  0 2141 223  800  600  samdesktop fish /home/sam
    #0x08e000f8  0 534  654  952  799  samdesktop *Untitled Document 1 - gedit
    #0x07200007  0 104  176  960  540  samdesktop AutoKey
    #0x04e00192  0 1618 428  300  650         N/A N/A
    #0x02000485  0 3840 0    1440 900  samdesktop Desktop
    #0x02000489  0 0    0    1920 1080 samdesktop nemo-desktop
    #0x0a200004  0 60   132  800  600  samdesktop fish /home/sam
    #Where the values are;
    #hexid, desktop, offsetx, offsety, sizex, sizey, hostname, window_title
    window = create_window()
    wmctrl = MagicMock(return_value = wmctrl_output)
    with patch("autokey.scripting.window.Window._run_wmctrl", wmctrl) as get_win_geom:
        assert expected == window.get_window_geom(hexid)


@pytest.mark.parametrize("wm_args, output",[
    ([], ""),
])
def test_window__run_wmctrl(wm_args, output):
    window = create_window()
    popen = MagicMock()
    with patch("subprocess.Popen", popen):
        output = window._run_wmctrl(wm_args)


