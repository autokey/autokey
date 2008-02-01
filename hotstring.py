#!/usr/bin/python
import os,sys,glob

# $Id$

# hotstring.py -- an example hotstring implementation on Linux

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import os,sys

try:
    import Xlib.X as X
    import Xlib.ext.xtest as xtest
    import Xlib.display as display
except ImportError:
    print "This program requires that python-xlib be installed."
    sys.exit(1)

import time
import autokey
import signal
#import pdb

# run a check to see if we're already running
user_folder = os.path.expanduser('~')
lock_file = os.path.join(user_folder, '.hotstring.lck')
if os.path.exists(lock_file):
    result = os.system('zenity --question --text="Waring! Stale lockfile; It looks like hotstring.py is already running, are you sure it isn\'t already active?"')
    if result: sys.exit(1)
else:
    open(lock_file, 'w')

# get rid of the program lock file
def cleanup(one = None, two = None):
    try:
        os.unlink(lock_file)
        os.system("killall hotstring_logger")
    except OSError: pass
    sys.exit(1)

# be sure to delete lock file on exit
signal.signal(signal.SIGHUP, cleanup)
signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

# Get abbrevs and see if there's an abbrev called event
autokey.update_abbr()
kbd_input_file = autokey.abbreviations.setdefault('eventfile','')

# hopefully the right keyboard device file is found

if not kbd_input_file:
    try:
        kbd_input_file = glob.glob('/dev/input/by-path/*kbd')[0]
    except IndexError:
        # hope for the best
        os.system("echo 'Cannot find event file!  Guessing, /dev/input/event1.  If this is wrong, hotstrings will not work!  Try and find out which /dev/input/eventX file your keyboard is attached to and make an abbrev called eventfile = /path/to/event/file | zenity --text-info")
        kbd_input_file = '/dev/input/event1'
capture_command = 'gksudo hotstring_logger %s' % kbd_input_file

# make the connections to the X server
disp = display.Display()
root = disp.screen().root

def send_backspace(root, amount):
    '''backspace out shortcut text'''
    for i in xrange(amount):
        xtest.fake_input(root, X.KeyPress, 22)
        xtest.fake_input(root, X.KeyRelease, 22)

# need to find a way to detect the keyboard layout...then the user
# wouldn't have to be asked about which translation table to use
qwerty = [ "", "<esc>", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
  "-", "=", "<backspace>",
  "<tab>", "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[",
  "]", "\n", "<control>", "a", "s", "d", "f", "g",
  "h", "j", "k", "l", ";", "'", "", "<shift>",
  "\\", "z", "x", "c", "v", "b", "n", "m", ",", ".",
  "/", "<shift>", "", "<alt>", " ", "<capslock>", "<f1>",
  "<f2>", "<f3>", "<f4>", "<f5>", "<f6>", "<f7>", "<f8>", "<f9>",
  "<f10>", "<numlock>", "<scrolllock>", "", "", "", "", "", "", "",
  "", "", "", "\\", "f11", "f12", "", "", "", "", "", "",
  "", "", "<control>", "", "<sysrq>"
]

# I use dvorak
dvorak = [ "", "<esc>", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
  "-", "=", "<backspace>",
  "<tab>", "'", ",", ".", "p", "y", "f", "g", "c", "r", "l", "/",
  "=", "\n", "<control>", "a", "o", "e", "u", "i",
  "d", "h", "t", "n", "s", "-", "", "<shift>",
  "\\", ";", "q", "j", "k", "x", "b", "m", "w", "v",
  "z", "<shift>", "", "<alt>", " ", "<capslock>", "<f1>",
  "<f2>", "<f3>", "<f4>", "<f5>", "<f6>", "<f7>", "<f8>", "<f9>",
  "<f10>", "<numlock>", "<scrolllock>", "", "", "", "", "", "", "",
  "", "", "", "\\", "f11", "f12", "", "", "", "", "", "",
  "", "", "<control>", "", "<sysrq>"
]

# prompt the user for proper translation table
layout = os.popen("/bin/echo -e qwerty\\\\ndvorak | zenity --list --title 'Choose keyboard layout' --column layout ").read()[:-1]
if layout == 'dvorak':
    keycodes = dvorak
elif layout == 'qwerty':
    keycodes = qwerty
else:
    sys.exit(1)

def watch_key(input, keycodes, pipe):
    '''grabs a key of input'''
    try: input += [(keycodes[int(pipe.readline()[:-1])])]
    except IndexError: pass # blank is okay
    # ignore blanks
    if input and input[-1] == '': input.pop()
    # ignore shift
    if input and input[-1] == '<shift>': input.pop()
    # duplicates are a problem
#     if input and input[-2:-1] == input [-1:]:
#         input.pop()

# loop variables
input = []                       # input stack
pipe = os.popen(capture_command) # keyboard pipe
ignore = False                   # flag to ignore input
                                 # until next non-word character

# set of things considered word characters
word_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'"

# loop until explicitly killed
while True:
    # value to hold text expansion
    value = ''
    # update abbreviations file
    autokey.update_abbr()
    # get rid of event abbrev
    try: del autokey.abbreviations['eventfile']
    except KeyError: pass

    print "Input after loop:", input

    # look at input
    watch_key(input, keycodes, pipe)

    # debug
    print "Input after key: ", input

    if input:
        # handle backspace
        if not ignore and input[-1] == "<backspace>":
            # get rid of the backspace event and the character before it
            input = input[:-2]

        # on non-word character, try expanding the abbreviation
        elif not input[-1] in word_chars:
            # if we were ignoring input, clear flag and input
            if ignore:
                ignore = False
                input = []
                continue
            # else, try to expand the abbreviation
            value = autokey.try_abbr(''.join(input[:-1]))
            current = input
            input = []
            if value:
                print "Sending '" + value + "'"
                print "Last value of current was: '" + current[-1] + "'"
                send_backspace(root, len(current))
                disp.flush()
                autokey.send_text(disp, root, value)
                # hack! sending the last value too soon seems to
                # randomly duplicate the character (sync problems
                # with X11)
                time.sleep(0.08)
                # send the last key and hope for the best.
                autokey.send_text(disp, root, current[-1])
                disp.flush()

        # if no possible match, blank out our tracked input
        elif not ignore and not autokey.possible_match(''.join(input)):
            ignore = True

# get rid of lockfile
cleanup()
