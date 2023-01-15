## Contents

* [Introduction](#introduction)
* [Case Changer](#caseChanger)
* [Choose Browser On Link Selection](#chooseBrowser)
* [Health Potion Drinker](#healthPotion)
* [Ask For Assistance](#askForAssistance)
* [Ask For A Cleric](#askForCleric)
* [Gnome Screenshot](#gnomeScreenshot)
* [Switch Or Start Firefox](#switchStartFirefox)
* [Toggle an Application](#toggleApplication)
* [RSS Zoomer](#rssZoomer)
* [Move Active Window](#moveActiveWindow)
* [Offline Print Queue](#offlinePrintQueue)
* [Key Wrapper](#keyWrapper)
* [WordPress Hebrew Concordance Linker](#wordpressHebrew)
* [Function to Type Text Slowly](#typeSlowly)
* [Function to list passwords on Firefox](#listPasswords)
* [Cycle case of selected text](#cycleCase)
* [Open a working directory](#openWorkingDirectory)
* [Simple IP Manager](#simpleIPManager)
* [Password Manager](#passwordManager)
* [SSH Manager](#sshManager)
* [Url Wrangler](#urlWrangler)
* [Googling query from anywhere](#googlinqQuery)
* [Search your phrases and scripts](#searchPhrasesScripts)
* [Dynamically assign hotkey actions](#dynamicallyAssign)
* [Push to talk](#pushToTalkScript)
* [Run an AutoKey script from another AutoKey script](#run-an-autokey-script-from-another-autokey-script)

## <a id="introduction" >Introduction
This page contains user-contributed scripts to demonstrate the **advanced** capabilities of AutoKey's scripting service.

Feel free to use the scripts presented for your own purposes. However, if you significantly modify them or come up with something new as a result of using them, please post them in [one of our community platforms](https://github.com/autokey/autokey/wiki/Community) so one of the wiki moderators can add them here for all to benefit.

All submitted scripts are publicly licensed as [GNU GPL v3](http://www.gnu.org/licenses/gpl.html)

For specific details on the custom functions available to AutoKey scripts, see the [API reference](https://autokey.github.io).

## <a id="caseChanger" />Case Changer ##
**Author**: [Kreezxil](https://kreezcraft.com)

**Description**: Grabs the selected text and changes it to upper case if lower or mixed case, and lower case if upper cased.

**Recommended Key**: <super>+c

```python
sample = clipboard.get_selection()
if sample.islower():
    keyboard.send_keys(sample.upper())
else:
    keyboard.send_keys(sample.lower())
```

## <a id="chooseBrowser" />Choose Browser On Link Selection ##

**Discovered at**: [Linux Journal](http://www.linuxjournal.com/content/autokey-desktop-automation-utility-linux)

**Author**: [Mike Diehl](http://www.linuxjournal.com/users/mike-diehl)

**Description**: This Autokey script takes a highlighted url from any program and triggers a selection of browsers from which you can choose to load the page.

```python
choices = ["konqueror", "firefox", "chrome"]
retCode, choice = dialog.list_menu(choices)
if retCode == 0:
  system.exec_command(choice + " " + clipboard.get_selection())
```

## <a id="healthPotion" />Health Potion Drinker ##

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

## <a id="askForAssistance" />Ask For Assistance ##

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

## <a id="askForCleric" />Ask For A Cleric ##

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

## <a id="gnomeScreenshot" />Gnome Screenshot ##

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

## <a id="switchStartFirefox" />Switch Or Start Firefox ##

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

## <a id="toggleApplication" />Toggle an Application ##

**Author**: mindfulsource

**Description**: this script toggles the primary window of any application like this example for Firefox. 'winClass' and binary path will vary depending on your scenario. Install 'xdotool' package if needed.

```python
#
import subprocess
command = 'wmctrl -lx'
output = system.exec_command(command, getOutput=True)

if 'Navigator.Firefox' in output:
    winClass = window.get_active_class()
    if winClass == 'Navigator.Firefox':
        system.exec_command("xdotool windowminimize $(xdotool getactivewindow)", getOutput=False)
    else:
        system.exec_command("wmctrl -xa Navigator.Firefox", getOutput=False)
else:
    subprocess.Popen(["/usr/bin/firefox"])
#
```


## <a id="rssZoomer" />RSS Zoomer ##

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

## <a id="moveActiveWindow" />Move Active Window ##

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

## <a id="offlinePrintQueue" />Offline Print Queue ##

**Author**: [Joe](http://groups.google.com/groups/profile?enc_user=wEhtURIAAAD4aTgqVkoh5XFntZCWEVBLD1eZzMt9YX5JjiuRxhHx-A)

**Description**: Changes `<ctrl>+p` for Mozilla applications to print to a file in a special offline print queue using incremented file names, intended for use with duplexpr.

```python
##print2file

## Copyleft 2012/08/31 - Joseph J. Pollock JPmicrosystems GPL
## Last Modified 2019/05/16 - Handle new Mozilla print dialog
##    Added support for Waterfox
##
## Assign <Super>+p for Firefox and Thunderbird
## to print to file in a special print queue using
## numbered file names, 01, 02, ... so the print jobs stay in order
##
## The new file name/number will have the same number of digits as the highest
## existing file name/number with left zero padding
## Two digit file names/numbers is the default.
##
## You can "seed" the process using e.g. touch 0000 in an empty print queue
## Intended for use with duplexpr
## http://sourceforge.net/projects/duplexpr/
##
## User must manually create print queue directory (~/pq)
##
## Not sure about the following still being necessary, but it works
## Set all *.print_to_filename variables in prefs.js (about:config)
## to path to print queue/01.ps (or .pdf)
## e.g. /home/shelelia/pq/01.ps (or .pdf)
##
## Using Ctrl+P as the hotkey doesn't seem to work in Firefox any more
## Hotkey <Super>+p
## Window Filter .*Thunderbird.*|.*Mozilla.*|.*Waterfox.*
##
## Changes <Super>+p to
## Print to file and looks at the print queue (~/pq) - hard coded
## Finds the last print file number and increments it by one
## Also handles files ending in ".pdf" or ".ps"
## Doesn't send final <Enter> so additional options like Print Selection
## can be set by the user

import os
import re
import string
import time

def filenum ():
    ## Gets next file number
    ## Set path to print queue
    home = os.getenv("HOME")
    path = home + "/pq"  ## Change this if your print queue is elsewhere
    ##print("path [" + path + "]")  ## debug
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
    digits = 2  ## default to 2-digit file numbers
    files = len(dirlist)
    if files > 0:
        i = 0
        ##print("Found [" + str(files) + "] files")  ## debug

        while (i < files) and (fn == ""):
            name = dirlist[i]
            ##print("name [" + name + "]")  ## debug
            ## regex for case insensitive replace of the last occurrence
            ## of .pdf or .ps at the end of the string with nothing
            ## if the file name has more than one, it's not one of ours
            name = re.sub(r'\.(?i)(pdf|ps)?$', "", name)
            ## Use the length of the one we found to set the zero padding length
            if name.isdigit():
                fn = str(int(name) + 1)
                digits = len(name)

            i += 1

    ## If no numeric file names were found
    if fn == "":
        fn="1"
        ##print("fn [" + fn + "]")

    ## left zero fill the file name to the same length as the one we found
    ##print("fn [" + fn + "] digits [" + str(digits) + "]")  ## debug
    fn = fn.zfill(digits)
    return fn

### DEBUG
## This code is for standalone testing outside of AutoKey

##output = filenum()
##print("Next File Number is [" + output + "]")
##quit()

### DEBUG

## Open the File menu
## Only works if Main Menu bar is displayed
## If we're not using Ctrl+p for the hotkey any more,
## maybe we can use it instead of AlT+f,p
##keyboard.send_keys("<alt>+f")
##time.sleep(1.0)
#### Select Print
##keyboard.send_keys("p")
##time.sleep(1.0)
keyboard.send_keys("<ctrl>+p")
time.sleep(1.0)

winTitle = window.get_active_title()

while (winTitle == "Printing"):
    time.sleep(1.0)
    winTitle = window.get_active_title()

## error window processing - for when FF complains about
## not being able to print all elements of the page
winTitle = window.get_active_title()
winClass = window.get_active_class()
if winTitle == "Printer Error" and winClass == "Dialog.Firefox":
   keyboard.send_keys("<enter>")
   time.sleep(1.0)

if winTitle == "Print Preview Error" and winClass == "Dialog.Firefox":
   keyboard.send_keys("<enter>")
   time.sleep(1.0)

if winClass == "Dialog.Firefox":
   keyboard.send_keys("<enter>")
   time.sleep(1.0)

## tab to the printer selection list, then to the top of the list
## which is the Print to File selection
keyboard.send_keys("<tab><home>")
time.sleep(2.0)
## tab to the file name field and enter the print queue directory path
keyboard.send_keys("<tab>")

output = filenum()

keyboard.send_keys("<enter>")
time.sleep(1.0)

keyboard.send_keys("<ctrl>+a") ## New 2019/04/23
time.sleep(1.0)

path = os.getenv("PQ") ## Change this if your print queue is elsewhere
path = "/home/bigbird/pq/"
keyboard.send_keys(path) ## New 2019/04/23
time.sleep(1.0)

## complete the file name field in the select file dialog
keyboard.send_keys(output)
keyboard.send_keys("<enter>")
time.sleep(1.0)

## Tab away from the File select button so the user can just press Enter
## But don't send an enter so the user can select
## other options before printing
keyboard.send_keys("<tab>")
time.sleep(0.5)
keyboard.send_keys("<tab>")


```

## <a id="keyWrapper" />Key Wrapper ##

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

## <a id="wordpressHebrew" />WordPress Hebrew Concordance Linker ##

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

## <a id="typeSlowly" />Function to Type Text Slowly ##

**Author**: Joseph Pollock - JPmicrosystems

**Description:***
Normally, AutoKey will emit characters from a phrase or script as fast as the system will allow. This is quite a bit faster than typing and some applications may not be able to keep up.

The following script emits/types a string of characters one at a time with a delay between each one.

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


## <a id="listPasswords" />Function to list passwords on Firefox ##

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



## <a id="cycleCase" />Cycle case of selected text ##

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

## <a id="openWorkingDirectory" />Open a working directory ##
**Author**: Kolibril13

**Description**: This script opens the working directory, which you define in "/home/username/Desktop/working_directory.txt" (Ubuntu 18.04)
```python
import os
with open('/home/kolibril/Desktop/working_directory.txt') as f:
        data = f.readlines()
working_directory= data[0]
working_directory = working_directory[:-2]
command = "nautilus " + working_directory
os.system(command)
```

## <a id="simpleIPManager" />Simple IP Manager ##
**Author**: [Kreezxil](https://kreezcraft.com)

**Description**: I created this to manage going to ip addresses that for whatever reason aren't named.
```python
from autokey.common import USING_QT

# Maybe you don't want to set up a name server or you got some sites
# you goto that are just ips, w/e the reason this works too.
ipaddresses = []
ipaddresses.append(["my system",  "127.0.0.1"])
ipaddresses.append(["Mom's PC",  "10.0.0.1", "default"])
ipaddresses.append(["John's Filth Can",  "10.0.0.1"])
# clearly mom needs lots of remote work and nobody goes near john's filth can

menuBuilder = []
defEntry = ""
menuEntry = "{} {}"
for x in ipaddresses:
  entry=menuEntry.format(x[0],x[1])
  if x.count("default") == 1:
      defEntry=entry
  menuBuilder.append(entry)

# Gtk seems to easily support dimensions whereas QT not so much
if USING_QT:
    retCode, choice = dialog.list_menu(menuBuilder, default=defEntry)
else:
    retCode, choice = dialog.list_menu(menuBuilder, height='800',width='350',default=defEntry)

if retCode == 0:
    selection="{}"
    keyboard.send_keys(selection.format(
        ipaddresses[
            menuBuilder.index(choice)
        ][1]
    ))
```

## <a id="passwordManager" />Password Manager ##

**Author**: [Kreezxil](https://kreezcraft.com)

**Description**: Post-it notes suck, writing on your hand sucks, using various adware loaded programs suck. Why not write your own password manager?

```python
from autokey.common import USING_QT

passMap1 = []

# you should only have one line where the 4th element has the world "default"
# the last line to have default in it will be the default in the list
# these are all local ips obviously and the passwords are stupid (3rd element)
# on purpose
# some entries look like they are being used for titles, they are, good eye!
passMap1.append( [  "category",  "title",  "" ])
passMap1.append( [  "       ",  "mom",  "makescookies", "default"])
passMap1.append( [  "       ",  "john", "mybrother"])

menuBuilder = []
defEntry = ""
menuEntry = "{} {} {}"
for x in passMap1:
  entry=menuEntry.format(x[0],x[1],x[2])
  if x.count("default") == 1:
      defEntry=entry
  menuBuilder.append(entry)

if USING_QT:
    retCode, choice = dialog.list_menu(menuBuilder, default=defEntry)
else:
    retCode, choice = dialog.list_menu(menuBuilder, height='800',width='350',default=defEntry)

if retCode == 0:
    selection="{}"
    keyboard.send_keys(selection.format(
        passMap1[
            menuBuilder.index(choice)
        ][2]
    ))
```

## <a id="sshManager" />SSH Manager ##

**Author**: [Kreezxil](https://kreezcraft.com)

**Description**: Similar to the password manager. As long as you have sshpass installed and you are in the terminal this script will save your fingers some major typing time.

**Edit**: September 26, 2021 - After using my own script for a long long time, I made some small improvements to it, that allow you to tap the primary key character for a username and jump to it. The ip is now hidden on the dropdown, and the menu shows the username in the first collumn. We're also now using a try except block to capture errors and allow the dialog to exit gracefully. Further, we can now use blank entries in our drop down.

```python
from autokey.common import USING_QT

#Required: sshpass
#        : and for you to be in the terminal already

# you should only have one line where the 4th element has the world "default"
# the last line to have default in it will be the default in the list
# these are all local ips obviously and the passwords are stupid (3rd element)
# on purpose
systems = []
systems.append( [ "","","" ])
systems.append( [ "","","GENERAL" ])
systems.append( [ "","","" ])
systems.append( [ "127.0.0.1",  "root",  "reallyhardpasswordnot",  "default"])
systems.append( [ "10.0.0.1",  "mom",  "makescookies"])
systems.append( [ "192.168.1.1",  "john",  "mybrother"])

menuBuilder = []
defEntry = ""
menuEntry = "{} {} {}"
hdrEntry = "====== {} ======"
for x in systems:
    if x[1] == "" and x[2] != "":
        entry = hdrEntry.format(x[2])
    elif x[1] == "" and x[2] == "":
        entry = ""
    else:
        entry = menuEntry.format(x[1], x[2], x[0])
        if x.count("default") == 1:
            defEntry = entry
    menuBuilder.append(entry)

# We use the boolean check to see which toolkit we're using
# the different toolkits receive extra parameters differently
try:
    if USING_QT:
        retCode, choice = dialog.list_menu(menuBuilder, default=defEntry)
    else:
        retCode, choice = dialog.list_menu(
            menuBuilder, height="800", width="350", default=defEntry
        )

    if retCode == 0:
        command = 'sshpass -p "{}" ssh -o StrictHostKeyChecking=no {}@{}'
        keyboard.send_keys(
            command.format(
                systems[menuBuilder.index(choice)][2]
                .replace("$", "\$")
                .replace("!", "\!"),
                systems[menuBuilder.index(choice)][1],
                systems[menuBuilder.index(choice)][0],
            )
        )
except:
    exit()
```

## <a id="urlWrangler" />Url Wrangler ##

**Author**: [Kreezxil](https://kreezcraft.com)

**Description**: If you follow me you know that I have 100 projects at https://www.curseforge.com/members/kreezxil/projects and that I am frequent updater of my modpacks. In order to build my changelogs after I copy the download link I use a hot key to trigger this device to help me paste a changelog.

```python
import time

data = clipboard.get_clipboard()
time.sleep(0.2)

if data=="":
    dialog.info_dialog("Empty","The Clipboard is empty!")
else:
    rawName = data[9:]
    parts = rawName.split("/")
    theLink = "https://{}/{}/{}/{}".format(parts[0],parts[1],parts[2],parts[3])
    changeLog = "{}/files/{}".format(theLink,parts[5])
    keyboard.send_keys("{}\n".format(changeLog))
```
## <a id="googlinqQuery" />Googling query from anywhere ##

**Author**: [Slothworks](https://askubuntu.com/a/685551/1058011)

**Description**: Being able to search any selected text by activating a python script (below) everytime I pressed a set of keyboard buttons.
```
import webbrowser
base="http://www.google.com/search?q="
phrase=clipboard.get_selection()

#Remove trailing or leading white space and find if there are multiple
#words.
phrase=phrase.strip()
singleWord=False
if phrase.find(' ')<0:
    singleWord=True

#Generate search URL.
if singleWord:
    search_url=base+phrase
if (not singleWord):
    phrase='+'.join(phrase.split())
    search_url=base+phrase

webbrowser.open_new_tab(search_url)
```

## <a id="searchPhrasesScripts" />Search your phrases and scripts ##

**Author**: [Caspx](https://github.com/caspx)

**Description**: This script will help you to quickly find those old sneaky phrases you can't seem to find.

```python
import os

from os import walk
from os.path import join


# very simple logger
def log(line):
    system.exec_command('echo "{}" >> /tmp/autokey.log'.format(line))


# Location to Autokey data dir - You can set it manually
USER = os.getenv('USER')
AUTOKEY_DATA_DIR = '/home/{}/.config/autokey/data'.format(USER)


# List all phrases and scripts located in the data dir
DATA_FILES = []
for (dirpath, dirnames, filenames) in walk(AUTOKEY_DATA_DIR):
    files = [join(dirpath, f) for f in filenames if f.endswith(('.txt', '.py'))]
    DATA_FILES.extend(files)


while True:
    ret_code, query = dialog.input_dialog(title="Search",
                                          message='Enter a query')
    if ret_code != 0:
        exit(1)

    # Currently check query against file path and name only
    candidates = {}
    query = query.lower()
    for f in DATA_FILES:
        if query in f.lower():
            path = f
            name = os.path.basename(f).split('.')[0]
            # known issue - May run over a phrase with the same name
            candidates[name] = path

    # show a dialog list with what we have found
    choices = candidates.keys()
    ret_code, choice = dialog.list_menu(choices,
                                        title='Search',
                                        text='Results',
                                        height="500",
                                        width="400")

    # Printing the selected phrase
    if ret_code == 0:
        path = candidates[choice]
        try:
            with open(path) as f:
                phrase = f.read()
            keyboard.send_keys(phrase)
        except Exception as e:
            pass

        exit(0)
    else:
        continue
```

## <a id="dynamicallyAssign" />Dynamically assign hotkey actions ##

**Author**: [tomrule007](https://github.com/tomrule007)

**Description**: Sample script that uses global value to toggle hotkey actions.

Enable script - sets enabled True and passes hotkey through.

```python
store.set_global_value("enabled", True)
keyboard.send_keys("<escape>")
```

Disable script - sets enabled False and passes hotkey through.

```python
store.set_global_value("enabled", False)
keyboard.send_keys(" ")
```

Action script - checks global value to determine action and also handles unset global with a default setting.

```python
try:
    enabled = store.get_global_value("enabled")
except TypeError:
    enabled = True #default setting

if enabled:
    # Do this if enabled.
else:
    # Do this if disabled.
```


## <a id="pushToTalkScript" />Push to Talk Script ##

**Author**: [Sid Coelho](https://www.linkedin.com/in/sidneydemoraes/)

**Description**: This script was made to allow a push-to-talk feature in applications that don't offer it natively such as Zoom.

```python
# This AutoKey script was made to allow a push-to-talk feature in applications that don't offer it natively such as Zoom.
# Do not forget to define your custom parameters, including the expected mute/unmute action, and to match the hotkey variable with the trigger hotkey defined for this script on AutoKey itself.
# P.S. I kept my debugging code commented out just for reference.

# Enter script code
import os

import evdev
    
# Defining some custom parameters
lockfile = '.p2t.lockfile'          # => You may choose whatever filename you like here. More details below.
device_path = '/dev/input/event6'   # => Be sure to check what input device corresponds to your keyboard with `python -m evdev.evtest`.
hotkey = 'KEY_F1'                   # => This hotkey should be the same one that triggers your script.
hold_action = 2
expected_action = '<alt>+A'         # => This is the expected key combination to trigger mute/unmute on the target app.

# Also, you can setup AutoKey to only trigger this script when your target app is open, based on the window title. In my case, I set it up with regex /*Reunião Zoom/.
#P.S. all lines that are entirely commented out were used for debugging and can be removed if you like.

try:
  open(lockfile)                                 # => If the lockfile exists, script does nothing. This is important because keeping a key pressed in fact sends several hits like you were typing it very quickly.
except FileNotFoundError:
  with open(lockfile, 'w'):                      # => Else, the script creates the lockfile and starts its magic.
    #print('Starting operation')
    #counter = 0
    
    device = evdev.InputDevice(device_path)      # => EvDev is used to access our keyboard.
    keyboard.send_keys(expected_action)          # => Here we send our "unmute" command to the target app.
    
    for event in device.read_loop():             # => And here we start monitoring the keyboard for keypress events.
      if event.type == evdev.ecodes.EV_KEY:      # => EvDev sends different types of events and this part ensures we'll check only for keypress events.
        category = evdev.categorize(event)       # => This is used to view the necessary event details.
        #print(category.keycode, type(category.keycode), category.keystate)
        
        if category.keycode != hotkey or category.keystate != hold_action: # => `keycode` is the pressed key itself and keystate represents one of the three possible actions: down, up or hold.
          break                                  # => If we detect that we are no longer holding the hotkey, break the loop.
          
        #counter += 1
        #print('Loop ', counter)
        #print(category.keycode, type(category.keycode), category.keystate)
    
  keyboard.send_keys(expected_action)            # => Here we issue the "mute" command to the target app.
  os.remove(lockfile)                            # => And remove the lockfile so as we can use the Push2Talk script again.
  #print('Ending operation')
```


## Run an AutoKey script from another AutoKey script ##

**Author**: Elliria

**Description**: AutoKey scripts can run other AutoKey scripts with the ```engine.run_script(...)``` API call. Note that putting a function into the calling script and then using parentheses on the engine API call to execute the function won't work, so it seems that all the work must be done within the called script, which means these will not function the way imported modules do.

1. Create an AutoKey script (the example uses the ```MyInternalScript``` script) with your contents in it (the example creates and runs a function):
```python
# Create a function:
def myFunction():
	# Display a dialog:
	dialog.info_dialog(message="This dialog was created by a function inside of another internal AutoKey script.")
# Run the above function:
myFunction()
```
2. Then create another AutoKey script and put these contents into it to call the first script:
```python
	engine.run_script("MyInternalScript")
```
When you run the second AutoKey script, the function in the first script is run and you get its output in the form of a dialog.
