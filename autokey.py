#!/usr/bin/python

# $Id$

# autokey.py -- text replacement shorcuts for any X desktop

# Copyright (C) 2008 Sam Peterson

# requires packages python-xlib
# sf.net page http://peabody.weeman.org/autokey.html

# Usage: autokey.py [ wait_time ]

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

import sys

try:
    import Xlib.X as X
    import Xlib.display as display
    import Xlib.ext.xtest as xtest
except ImportError:
    print 'This script requires the python-xlib library'
    print 'On Debian/Ubuntu: apt-get install python-xlib'
    sys.exit(1)

import os,re,ConfigParser,glob
import time
import signal
import string

#import pdb

# globals
abbreviations = {}

lock_file = ""

# structure to keep track of which modifier keys are on
modifier_keys = [["<control>", 0], ["<shift>", 0], ["<alt>", 0]]
mk = ("<control>", "<shift>", "<alt>")

# set of things considered word characters
word_chars = "`abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'"

# shifted values
shifted = '~!@#$%^&*()_{}?+"<>:'
orig_shifted = "`1234567890-[]/=',.;"
shifted_transtable = string.maketrans(orig_shifted,shifted)

# need to find a way to detect the keyboard layout...then the user
# wouldn't have to be asked about which translation table to use
qwerty = [ "", "<esc>", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
  "-", "=", "<backspace>",
  "<tab>", "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[",
  "]", "\n", "<control>", "a", "s", "d", "f", "g",
  "h", "j", "k", "l", ";", "'", "`", "<shift>",
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
  "d", "h", "t", "n", "s", "-", "`", "<shift>",
  "\\", ";", "q", "j", "k", "x", "b", "m", "w", "v",
  "z", "<shift>", "", "<alt>", " ", "<capslock>", "<f1>",
  "<f2>", "<f3>", "<f4>", "<f5>", "<f6>", "<f7>", "<f8>", "<f9>",
  "<f10>", "<numlock>", "<scrolllock>", "", "", "", "", "", "", "",
  "", "", "", "\\", "f11", "f12", "", "", "", "", "", "",
  "", "", "<control>", "", "<sysrq>"
]

user_folder = os.path.expanduser('~')
def get_abbr(file = user_folder + '/.abbr.ini'):
    parser = ConfigParser.ConfigParser()
    parser.readfp(open(file))
    return dict(parser.items('abbr'))

# timeout value to try
try: sleep_value = float(sys.argv[1])
except: sleep_value = 0.08

def make_lock_file():
    global lock_file
    # run a check to see if we're already running
    user_folder = os.path.expanduser('~')
    lock_file = os.path.join(user_folder, '.hotstring.lck')
    if os.path.exists(lock_file):
        result = os.system('zenity --question --text="Waring! Stale lockfile; It looks like hotstring.py is already running, are you sure it isn\'t already active?"')
        if result: sys.exit(1)
    else:
        open(lock_file, 'w')

# handler to get rid of the program lockfile
# has to take two arguments, even though it doesn't use them
def cleanup(one = None, two = None):
    try:
        os.unlink(lock_file)
    except OSError: pass
    os.system("espeak 'Autokey is exiting'")
    sys.exit(1)

# grab scroll lock shortcut key, FIXME: need to parameterize this
def grab_keys(display, root_window):
    root_window.change_attributes(event_mask = X.KeyPressMask)
    # set keyboard shortcut to f6
    root_window.grab_key(78, X.AnyModifier, 0, X.GrabModeAsync, X.GrabModeAsync)

# FIXME: in the future, this will be one of a set of functions which
# handle modifier keys.  The idea will be to turn off all modifier
# keys pressed, send the abbreviation, then turn back on all modifier
# keys that were pressed before the abbreviation.  I need to change
# somethings fundamentally in this program before implementing this.
def unset_modifiers(modifier_keys):
    for key in modifier_keys:
        pass

def check_modifiers(modifier_keys):
    pass

def reset_modifiers(modifier_keys):
    pass

def set_signal_handlers():
    # be sure to delete lock file on exit
    signal.signal(signal.SIGHUP, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

def make_capture_command():
    kbd_input_file = abbreviations.setdefault('eventfile','')
    # hopefully the right keyboard device file is found
    if not kbd_input_file:
        try:
            kbd_input_file = glob.glob('/dev/input/by-path/*kbd')[0]
        except IndexError:
            # hope for the best
            os.system("echo 'Cannot find event file!  Guessing, /dev/input/event1.  If this is wrong, hotstrings will not work!  Try and find out which /dev/input/eventX file your keyboard is attached to and make an abbrev called eventfile = /path/to/event/file | zenity --text-info")
            kbd_input_file = '/dev/input/event1'
    return 'gksudo hotstring_logger %s' % kbd_input_file

def send_backspace(root, amount):
    '''backspace out shortcut text'''
    for i in xrange(amount):
        xtest.fake_input(root, X.KeyPress, 22)
        xtest.fake_input(root, X.KeyRelease, 22)

def watch_key(input, keycodes, pipe):
    '''grabs a key of input'''
    try: input += [(keycodes[int(pipe.readline()[:-1])])]
    except IndexError: pass # blank is okay
    # ignore blanks
    if input and input[-1] == '': input.pop()
    # ignore duplicate shifts
    if input[-2:] == ['<shift>', '<shift>']:
        input.pop()

# text shortcuts read here
def update_abbr():
    global abbreviations
    try:
        abbreviations = get_abbr()
    except ConfigParser.ParsingError:
        os.system("zenity --info --text='You have errors in your abbr file'")
        cleanup()

def possible_match(input):
    global abbreviations
    input = translate_shifted(input)
    if '~' in input: return True
    for key in abbreviations.keys():
        # substring match
        if key[0:len(input)] == input:
            return True
    print "key not found, stopping input"
    return False

def translate_shifted(input):
    # filter modifiers (code to deal with modifiers will go here)
    shift_groups = input.split("<shift>")
    if len(shift_groups) > 1:
        # modify every even shift group
        for i in xrange(1, len(shift_groups), 2):
            shift_groups[i] = \
                shift_groups[i].translate(shifted_transtable)
        input = ''.join(shift_groups)
    return input

def try_abbr(input):
    global abbreviations
    # I'm hoping to add a command to quickly display all abbrs
    try:
        # translate shifted and remove modifiers
        input = translate_shifted(input)

        values = input.split('~')
        if len(values) > 1:
            try:
                return abbreviations[values[0]] % tuple(values[1:])
            except TypeError:
                os.system("zenity --error --text='Badly formmated abbr argument'")
                return ""
        elif '%%' in abbreviations[input]:
            try:
                firstpart, secondpart = abbreviations[input].split('%%')
                # count lefts and ups
                rows = secondpart.split('\n')
                left, ups = len(rows[0]), len(rows) - 1
                return (''.join([firstpart, secondpart]), (left, ups))
            except ValueError:
                os.system("zenity --error --text='Badly formmated abbr argument'")
                return ""
        else:
            return abbreviations[input]
    except KeyError: return ""

def stop_grab(display):
    display.ungrab_keyboard(X.CurrentTime)
    display.flush()

def send_left(display, root, num):
    for i in xrange(num):
        send_key(root, 100)

def send_up(display, root, num):
    for i in xrange(num):
        send_key(root, 98)

def send_text(display, root, text):
    new_text = escape_lines(text)
    # if shell expansion produced nothing, send nothing
    if new_text.isspace() and not text.isspace(): return
    print "escaped text was '%s'" % new_text
    print "Codes %s" % string2codes(display, new_text)
    for char in string2codes(display, new_text):
        send_key(root, char)

def escape_lines(text):
    # FIXME: need to escape all metacharacters
    text = text.replace('"','\\\"')
    text = os.popen('/bin/echo -e "%s"' % text).read()
    return text

def convert_code(display, keycode):
    return display.lookup_string(display.keycode_to_keysym(keycode, 0))

def string2codes(display, string):
    '''convert a string to a series of keycodes'''
    codes = []
    for letter in string:
        if letter.isupper() or letter in shifted:
            # hack! < doesn't print properly
            key = display.keysym_to_keycode(ord(letter))
            if key == 94: key = 25
            # tuple indicates key with modifier pressed
            codes.append((50,key))
        else:
            # int means regular keycode
            codes.append(display.keysym_to_keycode(ord(letter)))
        if codes[-1] == 0:
            # bad hack for now, make a newline
            codes[-1] = 36 # return key
    return codes[:-1]

def send_key(window, keycode):
    '''Send a KeyPress and KeyRelease event'''
    if type(keycode) == tuple:
        # send with modifier
        xtest.fake_input(window, X.KeyPress, keycode[0])
        xtest.fake_input(window, X.KeyPress, keycode[1])
        xtest.fake_input(window, X.KeyRelease, keycode[1])
        xtest.fake_input(window, X.KeyRelease, keycode[0])
    else:
        # send without modifier
        xtest.fake_input(window, X.KeyPress, keycode)
        xtest.fake_input(window, X.KeyRelease, keycode)

def check_toggle(display, root_window):
    result = False
    i = root_window.display.pending_events()
    while i > 0:
        event = root_window.display.next_event()
        if event.type == X.KeyPress: result = True
        i = i - 1
    return result

def main():
    # make the connections to the X server
    disp = display.Display()
    root = disp.screen().root
    make_lock_file()
    set_signal_handlers()

    # read abbreviations
    update_abbr()

    capture_command = make_capture_command()

    # loop variables
    input = []                       # input stack
    pipe = os.popen(capture_command) # keyboard pipe
    ignore = False                   # flag to ignore input
                                     # until next non-word character

    # prompt the user for proper translation table
    layout = os.popen("/bin/echo -e qwerty\\\\ndvorak | zenity --list --title 'Choose keyboard layout' --column layout ").read()[:-1]
    if layout == 'dvorak':
        keycodes = dvorak
    elif layout == 'qwerty':
        keycodes = qwerty
    else:
        sys.exit(1)

    # say hi to the world
    os.system("espeak 'Autokey is running' &")

    expansion_off = False

    grab_keys(disp, root)
    # loop until explicitly killed
    while True:
        # if expansion has been toggled off, ignore expansions
        exp_check = check_toggle(disp, root)

        # audio queue
        if exp_check and not expansion_off:
            os.system("espeak 'expansions off' &")
        elif exp_check and expansion_off:
            os.system("espeak 'expansions on' &")

        expansion_off = expansion_off ^ exp_check
        if expansion_off:
            # kill input keys
            watch_key(input, keycodes, pipe)
            input = []
            # be nice to the cpu
            time.sleep(0.01)
            continue
            
        # value to hold text expansion
        value = ''
        # update abbreviations file
        update_abbr()
        # get rid of event abbrev
        try: del abbreviations['eventfile']
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
            elif not input[-1] in word_chars and not input[-1] in mk:
                # if we were ignoring input, clear flag and input
                if ignore:
                    ignore = False
                    input = []
                    continue
                # else, try to expand the abbreviation
                value = try_abbr(''.join(input[:-1]))
                # get input buffer minus modifiers
                current = [x for x in input if x not in mk]
                input = []
                if value:
                    # code for sending events to X
                    print "Sending '" + str(value) + "'"
                    print "Last value of current was: '" + current[-1] + "'"
                    send_backspace(root, len(current))
                    disp.flush()
                    os.system("espeak 'expanding' &")
                    if type(value) == tuple:
                        send_text(disp, root, value[0])
                        send_up(disp, root, value[1][1])
                        send_left(disp, root, value[1][0])
                    else:
                        print "Whoa dude!"
                        send_text(disp, root, value)
                    # hack! sending the last value too soon seems to
                    # randomly duplicate the character (sync problems
                    # with X11)
                    time.sleep(sleep_value)
                    # send the last key and hope for the best.
                    send_text(disp, root, current[-1])
                    disp.flush()

            # if no possible match, blank out our tracked input
            elif not ignore and not possible_match(''.join(input)):
                ignore = True
    # get rid of lockfile
    cleanup()

# old code below, I don't want to delete this yet because it's a good
# example of how to setup a shortcut key.  I may use that in the
# future to setup a shortcut key to toggle expansion off and on.

def handle_keypress(abbreviations, display, root_window):
    '''Grabs the keyboard and listens for abbreviation sequence'''
    root_window.grab_keyboard(True, X.GrabModeAsync,
                              X.GrabModeAsync, X.CurrentTime)
    input = ""
    root_window.display.next_event() # get rid of key release

    event = root_window.display.next_event()
    if event.type == X.KeyRelease:
        if event.detail == 9:
            # Esc pressed, ungrab keyboard
            stop_grab(display)
            return
        # concatenate input
        input += str(convert_code(display, event.detail))
        # expand text if abbreviation matched
        if abbreviations.has_key(input):
            stop_grab(display)
            send_text(display, root_window, abbreviations[input])
            return
        # stop accepting keys if bad sequence typed
        if not possible_match(input):
            stop_grab(dispal)
            return

def old_main():
    print "Don't run this, run hotstring.py"
    sys.exit(1)
    disp = display.Display()
    root = disp.screen().root
    print "Press f6 in any window you wish to expand abbreviations in."
    print "Ctrl+C to quit"
    try:
        # loop until keyboard interrupt or explicit kill
        while True: 
            event = root.display.next_event() # should block until f6 pressed
            print "type shortcut sequence"
            # now grab the keyboard
            handle_keypress(abbreviations, disp, root)

    except KeyboardInterrupt:
        print 'Bye!'

if __name__ == '__main__': main()
