#!/usr/bin/python

# $Id$

# autokey.py -- text replacement shorcuts for any X desktop

# Copyright (C) 2008 Sam Peterson

# requires packages python-xlib and xmacro
# project tarball is now located at, be sure to get this from there
# http://peabody.weeman.org/autokey.tar.bz2

# This file is only maintained for its utility functions.  It was my
# first attempt at creating a text replacement tool for Linux and its
# code may still be useful so it has been left intact for the curious

# Usage: ./autokey.py

# go to the window where you want to type your shortcuts, press f6,
# then type an abbreviation.  If you misstype, press escape, then f6
# and try again.  this should work in any X11 application.

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

# TODO:
#  experiment with sending cursor keys, home, function keys, etc.
#
#  Probably should move abbreviations to a ConfigParse format file
#
#  Look into speeding up text insertion by maybe using the clipboard?
#
#  Look into dealing with selections and the clipboard
#
#  expand abbreviation functionality so it is more versatile, look into
#  variable length abbreviations
#
#  Find a way to present visual queues to the user, and maybe sound
#
#  find a way to send the shortcut key so it doesn't have to be effectively
#  "blacked out"

import os,re,keyreader,ConfigParser

try:
    import Xlib.X as X
    import Xlib.display as display
    import Xlib.ext.xtest as xtest
except ImportError:
    print 'This script requires the python-xlib library'
    sys.exit(1)

# tuple containing shifted values
shifted = ('~', '`', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '{', '}', '?', '+', '"', '<', '>', ':')

# text shortcuts read here
def update_abbr():
    global abbreviations
    try:
        abbreviations = keyreader.get_abbr()
    except ConfigParser.ParsingError:
        os.system("zenity --info --text='You have errors in your abbr file'")
update_abbr()

def possible_match(input):
    global abbreviations
    for key in abbreviations.keys():
        if key[0:len(input)] == input:
            return True
    print "key not found, stopping input"
    return False

def try_abbr(input):
    global abbreviations
    # I'm hoping to add a command to quickly display all abbrs
    try: return abbreviations[input]
    except KeyError: return ""

def stop_grab(display):
    display.ungrab_keyboard(X.CurrentTime)
    display.flush()

def send_text(display, root, text):
    text = escape_lines(text)
    print "Codes %s" % string2codes(display, text)
    for char in string2codes(display, text):
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
            # back hack for now
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

def handle_keypress(abbreviations, display, root_window):
    '''Grabs the keyboard and listens for abbreviation sequence'''
    root_window.grab_keyboard(True, X.GrabModeAsync,
                              X.GrabModeAsync, X.CurrentTime)
    input = ""
    root_window.display.next_event() # get rid of key release
    while True: # loop until explicit break
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
def main():
    print "Don't run this, run hotstring.py"
    sys.exit(1)
    disp = display.Display()
    root = disp.screen().root
    root.change_attributes(event_mask = X.KeyPressMask)
    # set keyboard shortcut to f6
    root.grab_key(72, X.AnyModifier, 0, X.GrabModeAsync, X.GrabModeAsync)
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
