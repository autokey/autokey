from unittest.mock import Mock, MagicMock, patch


import pytest
from hamcrest import *

from autokey.scripting import Window
from autokey.scripting.window import XRANDR_MONITOR_REGEX, WMCTRL_GEOM_REGEX

import re

wmctrl_out_1 = """0x04c00007  0 2164 608  752  599  samdesktop System Monitor
0x05600007  0 660  209  960  540  samdesktop AutoKey"""

wmctrl_out_2 = """0x02a00003  0 0    0    1920 1056 samdesktop Add more functions to window API by sebastiansam55 · Pull Request #471 · autokey/autokey — Mozilla Firefox
0x02a0004d  1 574  301  720  583  samdesktop (2702) Best of the Worst: Wheel of the Worst #20 - YouTube — Mozilla Firefox
0x04000007  1 2371 319  578  350  samdesktop Bluetooth Devices
0x04400004  0 3840 0    1440 876  samdesktop tmux /home/sam"""

wmctrl_out_3 = """0x07005700  0 60   132  1288 550  samdesktop craigslist
0x04c00004  0 725  241  800  600  samdesktop wmctrl /home/sam
0x08800007  0 228  234  652  579  samdesktop wmctrl-1.07.tar.gz [read only]
0x070201c3  0 200  272  1288 550  samdesktop wmctrl-1.07
0x08a000f8  0 418  424  952  799  samdesktop main.c (~/Applications/wmctrl-1.07) - gedit
0x08c00007  0 1980 132  960  540  samdesktop AutoKey"""

wmctrl_popen_out = b"""0x08a000f8  0 418  424  952  799  samdesktop main.c (~/Applications/wmctrl-1.07) - gedit
0x08c00007  0 1980 132  960  540  samdesktop AutoKey
"""

get_window_list_output_1 = [
    ("0x07200007", "0", "samdesktop", "AutoKey"),
    ("0x02000007", "0", "samdesktop", "Desktop"),
    ("0x08008500", "0", "samdesktop", "Firefox"),
    ("0x08c00007", "0", "samdesktop", "AutoKey")
]

# get_window_list_output_2 = 

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
    # is there an easy way to determine what the "signal" sent is?
    # looking at the wmctrl source code it sends _NET_CLOSE_WINDOW
    # which seems to just tell the window manager that the window should close
    # My initial impression reading the documentation was that wmctrl
    # was sending a "signal" like SIGKILL or SIGTERM
    pass

def test_window_resize_move():
    pass

def test_window_move_to_desktop():
    pass

def test_window_switch_desktop():
    pass


def test_window_set_property():
    pass

# @pytest.mark.parametrize("", [])
def test_window_get_active_geometry():
    # this function is a wrapper of get_window_geometry
    # it is covered by the tests for that function
    pass

# @pytest.mark.parametrize("", [])
def test_window_get_active_title():
    pass

# @pytest.mark.parametrize("", [])
def test_window_get_active_class():
    pass




#xrandr output:
####
#$ xrandr --listactivemonitors
#Monitors: 2
# 0: +*HDMI-0 1920/521x1080/293+0+0  HDMI-0
# 1: +DVI-D-0 1440/408x900/255+1920+0  DVI-D-0
####
# Notes: "Monitors" is always plural
# the asterik denotes the primary monitor
# 0: +*HDMI-0 1920/521x1080/293+0+0
#             ^^^^     ^^^^     ^ ^
# This is output from a 1920x1080 monitor
# the two zeros at the end represent the x and y offset from origin
# since this is the primary display they are both zero
xrandr_raw_double = """Monitors: 2
 0: +*HDMI-0 1920/521x1080/293+0+0  HDMI-0
 1: +DVI-D-0 1440/408x900/255+1920+0  DVI-D-0"""
xrandr_raw_single = """Monitors: 1
 0: +*DVI-D-0 1440/408x900/255+0+0  DVI-D-0"""

@pytest.mark.parametrize("title, xrandr_raw_output, matchClass, by_hex", [
    (None, (0, xrandr_raw_single), False, False), #single monitor
    (None, (0, xrandr_raw_double), False, False), #double monitor
    (":ACTIVE:", (0, xrandr_raw_double), False, False),
    ("AutoKey", (0, xrandr_raw_double), False, False),
])
def test_window_center_window(title, xrandr_raw_output, matchClass, by_hex):
    window = create_window()
    xrandr = MagicMock(return_value = xrandr_raw_output)
    with patch("autokey.scripting.window.Window.set_property") as set_prop, \
        patch("autokey.scripting.window.Window.resize_move") as resize_move, \
        patch("autokey.scripting.window.Window._run_xrandr", xrandr) as randr:
                window.center_window(title)
                # called with only checks the last time the method was called
                # set_prop.assert_called_with(title, "remove", "maximized_vert", matchClass=matchClass)
                # resize_move.assert_called_with(title, , , , )
                set_prop.assert_called_with(title, "remove", "maximized_horz", matchClass=matchClass, by_hex=by_hex)




@pytest.mark.parametrize("xrandr_output, regex_matches", [
    (xrandr_raw_single, [("1440", "900", "0", "0")]),
    (xrandr_raw_double, [("1920", "1080", "0", "0"),("1440", "900", "1920", "0")])
])
def test_xrandr_regex(xrandr_output, regex_matches):
    # there are 4 capture groups, in order from left to right
    # 1. width of monitor
    # 2. height of monitor
    # 3. x offset of monitor
    # 4. y offset of monitor
    # Below illustrates the intended captures
    # 0: +*HDMI-0 1920/521x1080/293+0+0
    #             ^^^^     ^^^^     ^ ^
    matches = re.findall(XRANDR_MONITOR_REGEX, xrandr_output, re.MULTILINE)
    assert matches == regex_matches




@pytest.mark.parametrize("wmctrl_output, func_output", [
    ((0, wmctrl_out_1), [
        ("0x04c00007", "0", "samdesktop", "System Monitor"),
        ("0x05600007", "0", "samdesktop", "AutoKey")
    ]),

])
def test_window_get_window_list(wmctrl_output, func_output):
    #the same wmctrl command is used for this function and get_window_geometry
    #see tests for get_window_geometry for more details on the regex used
    window = create_window()
    wmctrl = MagicMock(return_value = wmctrl_output)
    with patch("autokey.scripting.window.Window._run_wmctrl", wmctrl):
        print("func:",func_output)
        print("winoutput:",window.get_window_list())
        assert func_output == window.get_window_list()




@pytest.mark.parametrize("title, func_output, get_window_list_output",[
    ("AutoKey", "0x07200007", [("0x07200007", "0", "samdesktop", "AutoKey"),("0x02000007", "0", "samdesktop", "Desktop")]),
    ("Not Found", None, get_window_list_output_1)
])
def test_window_get_window_hex(title, func_output, get_window_list_output):
    window = create_window()
    get_window = MagicMock(return_value = get_window_list_output)
    with patch("autokey.scripting.window.Window.get_window_list", get_window):
        assert func_output == window.get_window_hex(title)
        # get_window.assert_called_with()




@pytest.mark.parametrize("window_title, by_hex, wmctrl_output, expected, active_title, hexid", [
    ("Bluetooth Devices", False, (0, wmctrl_out_2), [2371, 319, 578, 350], None, None),
    (":ACTIVE:",          False, (0, wmctrl_out_2), [3840, 0, 1440, 876], "tmux /home/sam", None),
    ("Cannot be found",   False, (0, wmctrl_out_3), None, None, None),
    ("String",            True,  (0, wmctrl_out_2), None, None, None),
    (":ACTIVE:",          True,  (0, wmctrl_out_2), [2371, 319, 578, 350], "Bluetooth Devices", "0x04000007"),
    ("0x04400004",        True,  (0, wmctrl_out_2), [3840, 0, 1440, 876], None, None),
])
def test_window_get_window_geometry(window_title, by_hex, wmctrl_output, expected, active_title, hexid):
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
    get_active = MagicMock(return_value = active_title)
    hex_fetch = MagicMock(return_value = hexid)
    with patch("autokey.scripting.window.Window._run_wmctrl", wmctrl) as get_win_geometry, \
         patch("autokey.scripting.window.Window.get_active_title", get_active) as get_active_title, \
         patch("autokey.scripting.window.Window.get_window_hex", hex_fetch) as get_window_hex:
        assert expected == window.get_window_geometry(window_title, by_hex)
        if window_title == ":ACTIVE:":
            get_active_title.assert_called()



@pytest.mark.parametrize("args, wmctrl_output, clean_output",[
    (["-l"], (b'output', b''), "outpu"),
    (["-lG"], (wmctrl_popen_out, b""), wmctrl_popen_out.decode()[:-1]),
])
def test_window__run_wmctrl(args, wmctrl_output, clean_output):
    window = create_window()
    # via https://stackoverflow.com/questions/53784239/python-unit-testing-mocking-popen-and-popen-communicate
    popen = MagicMock()
    # popen returns as bytes and returns a tuple in form of (stdout_data, stderr_data)
    popen.return_value.__enter__.return_value.communicate.return_value = wmctrl_output
    popen.return_value.__enter__.return_value.returncode = 0
    with patch("subprocess.Popen", popen), patch("subprocess.PIPE"):
        output = window._run_wmctrl(args)
        assert len(output) == 2
        # _run_wmctrl decodes bytes to string and strips the last character (usually a newline)
        assert output[1] == clean_output
        assert type(output[1]) == str
        assert output[0] == 0

def test_window__run_wmctrl_not_found():
    window = create_window()
    popen = MagicMock(side_effect=FileNotFoundError)
    with patch("subprocess.Popen", popen):
        assert window._run_wmctrl(["-lG"]) == (1, "ERROR: Please install wmctrl")


def test_window__run_xrandr_not_found():
    window = create_window()
    popen = MagicMock(side_effect=FileNotFoundError)
    with patch("subprocess.Popen", popen):
        assert window._run_xrandr(["--listactivemonitors"]) == (1, "ERROR: Please install xrandr")
