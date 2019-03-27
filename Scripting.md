# Introduction

This page contains some script examples to demonstrate the capabilities of AutoKey's scripting service.

For specific details on the custom functions available to AutoKey scripts, see the [API reference](https://autokey.github.io).

Porting your scripts from Python 2
==================================
Changes were made to source code to keep the scripting API stable. ``system.exec_command()`` returns a string. But if you use functions from the standard library you will have to fix that, as your script runs on a Python 3 interpreter. For example, expect subprocess.check_output() to return a bytes object.

[2to3](http://docs.python.org/dev/library/2to3.html) can be used to do automatically translate source code.

Some guides on porting code to Python 3:
 - http://python3porting.com/
 - http://www.diveintopython3.net/porting-code-to-python-3-with-2to3.html

# Basic Scripts

### Display Active Window Information

Displays the information of the active window after 2 seconds

    import time 
    time.sleep(2)
    winTitle = window.get_active_title()
    winClass = window.get_active_class()
    dialog.info_dialog("Window information", "Active window information:\\nTitle: '%s'\\nClass: '%s'" % (winTitle, winClass))

### Using Dates in Scripts

Users frequently need to use the date or time in a script.

The easiest way to get and process a date is by using the Python time or datetime modules.

    import time
    output = time.strftime("date %Y:%m:%d")
    keyboard.send_keys(output)

If you need a specific time other than "now", Python will be happy to oblige, but setting that up is a separate (purely Python) topic with many options. (See links at end.)

You can also do things like run the system date command.

This script uses the simplified system.exec_command() function to execute the Unix date program, get the output, and send it via keyboard output

    output = system.exec_command("date")
    keyboard.send_keys(output)

or, with more options

    commandstr="date "+%Y-%m-%d" --date="next sun""
    output = system.exec_command(commandstr)
    keyboard.send_keys(output)

but this creates another process and makes your script dependent on the behavior of the external command with respect to both its output format and any error conditions it may generate.

#### Background

Time itself is stored in binary format (from man clock_gettime(3)):

           All  implementations  support  the system-wide real-time clock, which is identified by CLOCK_REALTIME.  Its time represents
           seconds and nanoseconds since the Epoch.

Since this is essentially a really big integer, it is a handy form to use for calculations involving time. The Linux *date* command (and the Python *strftime()* function) understands this format and will happily convert from and to various other formats - probably using the same or a very similar *strftime* utility.

See:

datetime https://docs.python.org/3/library/datetime.html

time https://docs.python.org/3/library/time.html#module-time

for all the gory details.

### List Menu

This script shows a simple list menu, grabs the chosen option and sends it via keyboard output.

    choices = ["something", "something else", "a third thing"]
    retCode, choice = dialog.list_menu(choices)
    if retCode == 0:
        keyboard.send_keys("You chose " + choice)

## X Selection

This script grabs the current mouse selection, then erases it, and inserts it again as part of a phrase.

    text = clipboard.get_selection()
    keyboard.send_key("<delete>")
    keyboard.send_keys("The text %s was here previously" % text)

### Persistent Value

This script demonstrates 'remembering' a value in the store between separate invocations of the script.

    if not store.has_key("runs"):
        # Create the value on the first run of the script
        store.set_value("runs", 1)
    else:
        # Otherwise, get the current value and increment it 
        cur = store.get_value("runs")
        store.set_value("runs", cur + 1)

        keyboard.send_keys("I've been run %d times!" % store.get_value("runs")) ```

### Create new abbreviation

This script creates a new phrase with an associated abbreviation from the current contents of the X mouse selection (although you could easily change it to use the clipboard instead by using clipboard.get_clipboard()).

    # The sleep seems to be necessary to avoid lockups
    import time time.sleep(0.25)

    contents = clipboard.get_selection()
    retCode, abbr = dialog.input_dialog("New Abbreviation", "Choose an abbreviation for the new phrase")
    if retCode == 0:
        if len(contents) > 20:
            title = contents[0:17] + "..."
        else:
            title = contents
            folder = engine.get_folder("My Phrases")
            engine.create_abbreviation(folder, title, abbr, contents)

### Create new phrase

This is similar to the above script, but just creates the phrase without an abbreviation.

    # The sleep seems to be necessary to avoid lockups
    import time time.sleep(0.25)

    contents = clipboard.get_selection()
    if len(contents) > 20:
        title = contents[0:17] + "..."
    else:
        title = contents
        folder = engine.get_folder("My Phrases")
        engine.create_phrase(folder, title, contents)

### Start external scripts

In case you've some bash-scripts or just want to start a program with shortcuts
To start a script

    import subprocess 
    subprocess.Popen(["/bin/bash", "/home/foobar/bin/startfooscript.sh"])

To start a program with wine. 

    import subprocess 
    subprocess.Popen(["wine", "/home/foobar/wine/program/some.exe"])


# Advanced Scripts

This page contains user contributed scripts to demonstrate the **advanced** capabilities of AutoKey's scripting service.

Feel free to use the scripts presented for your own purpose. However, if you significantly modify them or come up with something new as a result of using them please post them into our forums so one of the wiki moderators can install them here for all to benefit.

All submitted scripts are publicly licensed as [GNU GPL v3](http://www.gnu.org/licenses/gpl.html)

For specific details on the custom functions available to AutoKey scripts, see the [API reference](https://autokey.github.io).

### Choose Browser On Link Selection ###

**Discovered at**: [Linux Journal](http://www.linuxjournal.com/content/autokey-desktop-automation-utility-linux)

**Author**: [Mike Diehl](http://www.linuxjournal.com/users/mike-diehl)

**Description**: This Autokey script takes a highlighted url from any program and triggers a selection of browsers from which you can choose to load the page.

```python
choices = ["konqueror", "firefox", "chrome"]
retCode, choice = dialog.list_menu(choices)
if retCode == 0:
  system.exec_command(choice + " " + clipboard.get_selection())
```

### Health Potion Drinker ###

**Author**: [Itscool - Al](http://www.bowierocks.com)

**Description**: I created this Autokey script to help me manage the drinking of health potions. The game lacks a mechanism to quickly imbibe a potion without some difficulty. It is far easier to hit one key that does it for you. In the case of this script, you are also taken back to safe zone if you are out of health potions. All you have to do is make sure you have pot in all of your slots. It will work even if you don’t have pot in all of the slots. For use with the flash client at [Realm of the Mad God](http://www.realmofthemadgod.com).

```python
if not store.has_key("heal"):
# set the key 'persistant variable' if we don’t have it already
store.set_value("heal",1)

pot = store.get_value("heal")
if pot > 8:
  # also send us back to the nexus
  pot = 1
  keyboard.send_key("<f5>")

#do the pot thing
output = str(pot)
keyboard.send_key(output)
#increment the pot

pot = pot + 1

store.set_value("heal",pot)
```

### Ask For Assistance ###

**Author**: [Itscool - Al](http://www.bowierocks.com)

**Description**: I created this Autokey script to do two things. 1) Generate a randomized shout message to gain assistance and 2) drink a manna pot from one of the bottom four inventory slots. For use with the flash client at [Realm of the Mad God](http://www.realmofthemadgod.com).

```python
from random import randrange
announcement = ["OMG","","DARN","","OH BOY","","COME HERE","","TP ME","","MESHUGANA","","OY",""]
declaration = ["I could seriously use some help here","The devs must be crazy","How many minions did Oryx say he had to feed?","Dodge bullets? Sure. But this","MONSTERS"]
expletives = ["!","!!","!!!","!!!!1","!!!1!","!!1!1!"]

if not store.has_key("mana"):
    # set the key 'persistant variable' if we don't have it already
    # or if the value is greater than 8 reset it to 5
    store.set_value("mana",5)

mana = store.get_value("mana")
if mana > 8:
    mana = 5

part1 = announcement[randrange(len(announcement))]
part2 = declaration[randrange(len(declaration))]

if part1 != "":
    part1 = part1 + expletives[randrange(len(expletives))]
if part2 != "":
    part2 = part2 + expletives[randrange(len(expletives))]

output = "/yell " + part1 + " " + part2 + "\n"
keyboard.send_keys(output)

#do the mana thing
output = str(mana)
keyboard.send_key(output)
#increment the mana
mana = mana + 1
store.set_value("mana",mana)
```

### Ask For A Cleric ###

**Author**: [Itscool - Al](http://www.bowierocks.com)

**Description**: I created this Autokey script will help you manage drinking health potions in the top four inventory slots. Additionally it'll generate a random yell asking for some type of healing support. For use with the flash client at [Realm of the Mad God](http://www.realmofthemadgod.com).

```python
from random import randrange
announcement = ["HELP","","HP","","HEAL","","MEDIC","","DR. WHO","","1-800-PRIEST",""]
declaration = ["I could use some professional help here","Anyone in the businesses of hp","Bring lots of that RED STUFF in a jar","I don't wanna die","Mommy","You can leave a msg at GHOSTBUSTERS","I'm going to meet the maker","Great, I'm another Father Dowling Mystery","Agatha Christi?! Posh","Should've listened to Momma","I don't want this chocolate","..."]
expletives = ["!","!!","!!!","!!!!1","!!!1!","!!1!1!"]

if not store.has_key("pot"):
    # set the key 'persistant variable' if we don't have it already
    # or if the value is greater than 4 reset it to 1
    store.set_value("pot",1)

pot = store.get_value("pot")
if pot > 4:
    pot = 1

part1 = announcement[randrange(len(announcement))]
part2 = declaration[randrange(len(declaration))]

if part1 != "":
    part1 = part1 + expletives[randrange(len(expletives))]

if part2 != "":
    part2 = part2 + expletives[randrange(len(expletives))]

output = "/yell " + part1 + " " + part2 + "\n"
keyboard.send_keys(output)

#do the pot thing
output = str(pot)
keyboard.send_key(output)
#increment the pot
pot = pot + 1
store.set_value("pot",pot)
```

### Gnome Screenshot ###

**Author**: [Dave](http://groups.google.com/groups/profile?enc_user=gy_J_BYAAABLTVwIPyUi9oJFSRwGwC70o4cocwWvDVg2RHsu8f1bCg)

**Description**: The Autokey script created here will allow you to quickly screenshot your desktop while moving your mouse off to the right. Dave had originally submitted it to the group forums there and at least 4 of us helped him to modify it and make it faster.

```python
#
# replace ~/Downloads with the location of where you told gnome-screenshot to save the pic
#
system.exec_command("bash -c 'rm ~/Downloads/today.png'",False)
system.exec_command("gnome-screenshot -w", False)
window.wait_for_exist("Save Screenshot", timeOut=5)
system.exec_command("xte 'mousemove 725 399'", False)
window.activate("Save Screenshot", switchDesktop=False)
keyboard.send_keys("today")
```

### Switch Or Start Firefox ###

**Author**: Jack

**Description**: this script switches to the Firefox window. if Firefox is not already running, the script starts it. i use similar scripts for the applications i use most.

```python
#
#start firefox or switch to firefox
import subprocess
command = 'wmctrl -l'
output = system.exec_command(command, getOutput=True)

if 'Firefox' in output:
    window.activate('Firefox',switchDesktop=True)

else:
    subprocess.Popen(["/usr/bin/firefox"])
#
```

### RSS Zoomer ###

**Author**: Jack

**Description**: several actions to go on the same key… i have this on this script sends `'^+'` when in Firefox or Chromium to do a zoom in. when i'm reading RSS feeds in Akregator, it sends `'='` to move to the next unread item.

```python
#

winTitle = window.get_active_title()

if 'Mozilla Firefox' in winTitle:
    output = "+"
    keyboard.send_keys(output)

elif 'Chromium' in winTitle:
    output = "+"
    keyboard.send_keys(output)

elif 'Akregator' in winTitle:
    output = "="
    keyboard.send_keys(output)

else:
    output = ""
    keyboard.send_keys(output)

#
```

### Move Active Window ###

**Author**: Jack

**Description**: here are 4 tiny scripts to move the active window left, right, up, down. fwiw i have them on !Super+AppropriateArrow.

**Move Window Left**:
```python
# move active window left
thisWin = window.get_active_title()
windetails = window.get_active_geometry() # returns tuple of: x, y, width, height
newX = windetails[0] - 40
window.resize_move(thisWin, xOrigin=newX, yOrigin=-1, width=-1, height=-1, matchClass=False)
```

**Move Window Right**:
```python
# move active window right
thisWin = window.get_active_title()
windetails = window.get_active_geometry() # returns tuple of: x, y, width, height
newX = windetails[0] + 40
window.resize_move(thisWin, xOrigin=newX, yOrigin=-1, width=-1, height=-1, matchClass=False)
```

**Move Window Up**:
```python
# move active window up
thisWin = window.get_active_title()
windetails = window.get_active_geometry() # returns tuple of: x, y, width, height
newY=windetails[1] - 80 # must bigger than approx 40, otherwise window moves down!
window.resize_move(thisWin, xOrigin=-1, yOrigin=newY, width=-1, height=-1, matchClass=False)
```

**Move Window Down**:
```python
# move active window down
thisWin = window.get_active_title()
windetails = window.get_active_geometry() # returns tuple of: x, y, width, height
oldY = windetails[1]
newY=windetails[1] + 20
window.resize_move(thisWin, xOrigin=-1, yOrigin=newY, width=-1, height=-1, matchClass=False)
```

### Offline Print Queue ###

**Author**: [Joe](http://groups.google.com/groups/profile?enc_user=wEhtURIAAAD4aTgqVkoh5XFntZCWEVBLD1eZzMt9YX5JjiuRxhHx-A)

**Description**: Changes `<ctrl>+p` for Mozilla applications to print to a file in a special offline print queue using incremented file names, intended for use with duplexpr.

```python
# print2file

import time
import os

## Copyleft 2012/02/27 - JPmicrosystems GPL
## Change <ctrl>+p for Firefox and Thunderbird
## to print to file in a special print queue using
## numbered file names, 01, 02, ... so the print jobs stay in order
## Intended for use with duplexpr
## http://sourceforge.net/projects/duplexpr/
## User must manually create print queue folder (~/pq)
## and set all *.print_to_filename variables in prefs.js (about:config)
## to path to print queue/01.ps
## e.g. /home/shelelia/pq/01.ps

## Hotkey <ctrl>+p
## Window Filter .*Mozilla.*

## Changes <ctrl>+p to
## Print to file and looks at the print queue (~/pq)
## Finds the last print file number and increments it by one
## Doesn't send final <Enter> so additional options like Print Selection
## can be set by the user
##Fails if Loading file to print takes longer than the second delay

def filenum ():
    ## Gets next file number
    ## Set path to print queue
    path = os.getenv("HOME") + '/pq'
    ## Get all the files in the print queue in a list
    ## Handle filesystem error
    try:
        dirlist=os.listdir(path)
    except:
        return "EE"

    ## And sort it in reverse order
    ## So the largest numbered file is first
    dirlist.sort(reverse=True)

    ## If there aren't any files then
    ## Set last file to 0
    ## else, set it to the last file with a valid number
    ## Defend script against non-numeric file names
    ## go down the reverse sorted list until a numeric one is found
    fn=""
    if len(dirlist) == 0:
      fn = "00"
    else:
        files = len(dirlist)
        i = 0
        while (i < files) and (fn == ""):
            name = dirlist[i]
            if name.isdigit():
                fn = str(int(name) + 1)
            i += 1

    if fn == "":
      fn = "01"

    ## If it's less than 2 characters long,
    ## Left pad it with a zero
    ## To maintain the sorting order
    if len(fn) < 2:
      fn = '0' + fn

    return fn


## Open the File menu
## (can't use <ctrl>+p because that's the hotkey)
keyboard.send_keys("<alt>+f")
time.sleep(1.0)
## Select Print
keyboard.send_keys("p")
time.sleep(2.0)
## tab to the printer selection list, then to the top of the list
## which is the Print to File selection
keyboard.send_keys("<tab><home>")
time.sleep(2.0)
## tab to the file name field and enter the print queue directory path
keyboard.send_keys("<tab>")

output = filenum()

## complete the file name field in the print dialog
## But don't send an enter so the user can select
## options before printing
keyboard.send_keys(output)


```

### Key Wrapper ###

**Author**: [tpower21](http://groups.google.com/groups/profile?enc_user=x6tfARIAAAAifj82FffFIj7Xx_wp_F3B8rhlH0Pnl47z4AZhN98BFg)

**Description**: Wrap selected text with one or two keys/sets of keys, or
output them if nothing's selected, and keep your current clipboard.
Can call it using engine.run\_script(description) then bind
whatever's calling it to something.

**Real World Use**: Highlight a load of text and that you need wrapped in something. Possibly say quotes, brackets, braces, parens, pipes, asterisks etc ... That is why the script is in two parts so you can have multiple assignments to the same engine.

**Alternate Use**: Wrapping a load of text with words or phrases like you would use in html, xml, etc ... where _wrap_ could be `<div>` and _`wrap_close`_ could be `</div>`.

**binder script**:
```python
wrap = "<shift>+9" 
wrap_close = "<shift>+0" 
engine.run_script("wrap_selection")
```

**script**: wrap\_selection
```python
# wrap_selection 
# get keys 
try: 
    wrap 
except NameError: 
    dialog.info_dialog("Need at least one key to wrap selection with.") 
try: 
    wrap_close 
except NameError: 
    wrap_close = wrap 
# below needed to get working in some apps, otherwise 
# clipboard.get_selection() quicker/better 
# get clipboard/selection 
try: 
    clip_board = clipboard.get_clipboard() 
except: 
    clip_board = "" 
keyboard.send_keys("<ctrl>+x") 
time.sleep(0.01) 
try: 
    selection = clipboard.get_clipboard() 
except: 
    selection = "" 
# clipboard won't update if selection empty 
if clip_board == selection: 
    selection = "" # problem if clipboard and selection are the same 
# and not empty, but not the end of the world 
# wrap and clean up 
keyboard.send_keys(wrap+selection+wrap_close+"<left>")
#tpower21 added the following two lines on February 7 2012
for s in selection:
   keyboard.send_keys("<shift>+<left>") 
clipboard.fill_clipboard(clip_board) 
del clip_board, selection, wrap, wrap_close 
```

### WordPress Hebrew Concordance Linker ###

**Author**: [Itscool - Al](http://www.bowierocks.com)

**Description**: This AutoKey script takes a selected entry in your WordPress article that may or may not contain parens "()", extracts the number enclosed and converts that to a link to the concordance at eliyah.com. The number is assumed to be a HEBREW lexicon indicator as pertains to the Strong's Concordance that is keyed to the New King James Bible. I have my hot-key combo set to "`<alt>+<shift>+h`". With no further ado I present the following Python script for AutoKey that does what I claim.

```python
selection = clipboard.get_selection()
if selection[0] == "(":
    selection = selection[1:-1]
 
if selection[-1] == ")":
    selection = selection[0:-2]
    
keyboard.send_keys("<alt>+<shift>+a")
 
keyboard.send_keys("http://www.eliyah.com/cgi-bin/strongs.cgi?file=hebrewlexicon&isindex=%s" % selection)
keyboard.send_keys("<tab>")
keyboard.send_keys("Strong's Concordance HEBREW %s" % selection)
keyboard.send_keys("<enter>")
```

### Function to Type Text Slowly ###

**Author**: Joseph Pollock - JPmicrosystems

**Description:***
Normally, AutoKey will emit characters from a phrase or macro as fast as the system will allow. This is quite a bit faster than typing and some applications may not be able to keep up.

The following macro emits/types a string of characters one at a time with a delay between each one.

The first parameter is the string of characters to type. The second optional parameter is the number of seconds to delay between each keypress. It defaults to 0.1 seconds.

```python

import time

## Type a string character by character
##   from within AutoKey
##   with a small delay between characters
def type_slow(string, delay=0.1):
    if delay <= 0:
        # No delay, directly relay the whole string to the API function.
        keyboard.send_keys(string)
    else:
        for c in string:
            keyboard.send_keys(c)
            time.sleep(delay)
```


### Function to list passwords on Firefox ###

**Author**: Chris Dardis

**Description:***
This brings up your list of saved passwords at a keystroke e.g. "CTRL + ALT + p" while using Firefox. 
This comes in handy on a daily basis for me.
There is a limit to how fast this will work, as it involves tabbing on an active browser. 
Thus, the values for time.sleep() below are perhaps a little conservative. 

```python

## menu - edit
keyboard.send_keys("<alt>+e")
time.sleep(0.5)
## menu - preferences (opens new tab)
keyboard.send_keys("n")
time.sleep(0.5)
keyboard.send_keys("passwords")
time.sleep(1.5)
keyboard.send_keys("<tab>")
time.sleep(0.25)
keyboard.send_keys("<tab>")
time.sleep(0.25)
keyboard.send_keys("<enter>")
time.sleep(1.0)
keyboard.send_keys("<tab> <tab> <tab>")
time.sleep(2.0)
keyboard.send_keys("<tab>")
time.sleep(0.5)
keyboard.send_keys("<enter>")
time.sleep(1.0)
window.activate("Confirm")
time.sleep(1.0)
keyboard.send_keys("<alt>+y")
time.sleep(2.0)
## x7 total
keyboard.send_keys("<tab>")
keyboard.send_keys("<tab>")
keyboard.send_keys("<tab>")
keyboard.send_keys("<tab>")
keyboard.send_keys("<tab>")
keyboard.send_keys("<tab>")
keyboard.send_keys("<tab>")

```



### Cycle case of selected text ###

**Author**: Jack

**Description**: This script changes the case of selected text. Repeated runs to this script cycle through Uppercase, Title Case, Lowercase:

    HELLO WORLD
    Hello World
    hello world

```python
# 
# Change case of selected text. Repeated runs to this script cycle through Uppercase, Title Case, Lowercase:
#   HELLO WORLD, Hello World, hello world
#
# jack

# Get the current selection.
sText=clipboard.get_selection()
lLength=len(sText)

try:
    if not store.has_key("textCycle"):
        store.set_value("state","title")

except:
    pass
    
# get saved value of textCycle
state = store.get_value("textCycle")

#dialog.info_dialog(title='state', message=state)


# modify text and set next modfication style
if state == "title":
    sText=sText.title()
    newstate = "lower"

elif state == "lower":
    sText=sText.lower()
    newstate = "upper"

elif state == "upper":
    sText=sText.upper()
    newstate = "title"

else:
    newstate = "lower"

# save for next run of script
store.set_value("textCycle",newstate)    
    
    
  
# Send the result.
keyboard.send_keys(sText)
keyboard.send_keys("<shift>+<left>"*lLength)

```
