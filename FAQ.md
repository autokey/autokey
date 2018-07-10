### What are the dependency packages for AutoKey?
On Debian or Ubuntu you can get the dependencies by typing:

	sudo apt-get install python-gtk2
	sudo apt-get install python-gtksourceview2
	sudo apt-get install python-glade2
	sudo apt-get install python-xlib
	sudo apt-get install python-notify
	sudo apt-get install python-pyinotify
	sudo apt-get install wmctrl

Note that if you installed AutoKey from a .deb or using apt-get, these dependencies will automatically be installed for you.

It is quite possible that you get more runtime errors requiring you to further add packs manually.

### What is the license of AutoKey?
AutoKey is published under GNU GPL v3 license.

### X protocol errors on launch! 
```X protocol error:
<class 'Xlib.error.BadAccess'>: code = 10, resource_id = 260, sequence_number = 17, major_opcode = 33, minor_opcode = 0
```
Most likely Autokey has indeed started, and these are just benign messages from python-xlib. Verify that autokey is running with `ps aux | grep autokey`
### Does AutoKey work with scripts which were written with the popular AutoHotKey Windows application?
No. AutoKey's built-in Python scripting is arguably much more powerful than the AHK language and makes it possible to do many of the things that AutoHotKey? scripts can do on Windows, in addition to some things AHK doesn't support.

### Is AutoKey available on Microsoft Windows?
No. There are similar alternatives on Windows like [PhraseExpress](http://www.phraseexpress.com/) and [AutoHotKey](http://www.autohotkey.com/)

### Can I temporarily suspend/resume AutoKey?
To toggle !Autokey from suspend/resume, use the hotkey which you have specified in Settings -> Advanced Settings -> Special Hotkeys->Use a hotkey to toggle expansions. Alternatively this can be controlled from the system tray Autokey popup menu.

### What are the trigger characters?
The default trigger characters are dependent on your locale. They are any characters that are not normally considered part of a word. For English locales, these are characters like Enter (Return), Tab, Space and punctuation, among others.

### Can I use Caps Lock in Autokey?
1.  Disable caps lock:

`xmodmap -e 'clear Lock'`

2. Use xcape to assign a key sequence e.g. Left super+f

`xcape -e '#66=Super_L|f'`

3. Attach autokey script to the assigned key sequence.

4. Reassign capslock to (say) pressing both shift keys.

`setxkbmap -option "caps:none"`
`setxkbmap -option "shift:both_capslock"`

Caps lock key is really out of autokey's scope, you just need to use other utilities to get the desired effect.

### Where is my configuration information stored? Can I move those to other machines?
By default AutoKey stores your settings under ~/.config/autokey. You can of course create AutoKey folders anywhere you wish as well, using "Create New Top-Level Folder". Folders containing phrases and scripts can be freely copied between machines using your favourite file manager, or synchronised using a program such as Dropbox. Please remember to also copy the hidden files as each macro and phrase has one.

### Using Dates in Macros

Users frequently need to use the date or time in a macro.

The easiest way to get and process a date is by using the Python time or datetime modules.

    import time
    output = time.strftime("date %Y:%m:%d")
    keyboard.send_keys(output)

If you need a specific time other than "now", Python will be happy to oblige, but setting that up is a separate (purely Python) topic with many options. (See links at end.)

You can also do things like run the system date command 

    commandstr="date "+%Y-%m-%d" --date="next sun""
    output = system.exec_command(commandstr)
    keyboard.send_keys(output)

but this creates another process and makes your macro dependent on the behavior of the external command with respect to both its output format and any error conditions it may generate.

Background

Time itself is stored in binary format (from man clock_gettime(3)):

           All  implementations  support  the system-wide real-time clock, which is identified by CLOCK_REALTIME.  Its time represents
           seconds and nanoseconds since the Epoch.

Since this is essentially a really big integer, it is a handy form to use for calculations involving time. The Linux *date* command (and the Python *strftime()* function) understands this format and will happily convert from and to various other formats - probably using the same or a very similar *strftime* utility.

See:

datetime https://docs.python.org/3/library/datetime.html

time https://docs.python.org/3/library/time.html#module-time

for all the gory details.
