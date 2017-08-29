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

### What is the license of AutoKey?
AutoKey is published under GNU GPL v3 license.

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
By default AutoKey stores your settings under ~/.config/autokey. You can of course create AutoKey folders anywhere you wish as well, using "Create New Top-Level Folder". Folders containing phrases and scripts can be freely copied between machines using your favourite file manager, or synchronised using a program such as Dropbox.
