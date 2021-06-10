See [[Scripting#advanced-scripts]].

## Url Displayer
- **Author**: [Kreezxil](https://kreezcraft.com)
- **Purpose**: Use a dictionary (associative array) to manage a list of urls using short names
- **Notes**: now discerns if a browser is being used, if you give it the browsers you use.

```python
# you can click in a chatEntity like discord and this will make a newline without forcing the message, which is intended behavor
# but you can click in the url bar of a browser and use it and it will make a new page/tab without forcing a new browser shift+enter

def printUrl(part):
    clipboard.fill_clipboard("{}".format(part))
    time.sleep(0.2)
    keyboard.send_keys("<ctrl>+v"+newline)
    time.sleep(0.1)

urlBook = {}
urlBook.append("Vacations","https://disney.com")
urlBook.append("Politics", "https://whitehouse.gov")
urlBook.append("Steam Alternative","https://itch.io")

# The shift enter is for Discord and other chat mechanisms, so we'll scan for an app to exempt.
# Add the browsers or apps you use to exempt them from the shift enter issue.
# Oh you don't know. If you put an address in a url box and hit shift enter it opens a new
# window!

exemption=[]
exemption.append("Chrome")
exemption.append("Firefox")
exemption.append("Edge")
exemption.append("Brave")

targetScan = window.get_active_title()

# There maybe an easier way to do this, in fact I'm sure of it, because Python is the language that
# deals with lists, if you know of it or discover please update the wiki entry.
# Or shoot me a message on Gitter or our Discord.

newline = "<shift>+<enter>" # Our default
for test in exemption:
    if targetScan.find(test) > -1:
        #dialog.info_dialog(title="Info",message="Found "+test)
        time.sleep(0.2)
        newline="<enter>"
        break

choices = list(urlBook.keys())
choices.sort()
choices.insert(0,"All")

retCode, choice = dialog.list_menu( title="urlBook!",options=choices )
if retCode == 0:
    if choice == "All":
        urls = list(urlBook.values())
        urls.sort()
        count=1
        for element in urls:
            printUrl("{}: {}".format(count,element))
            count+=1
            if count%10==0:
                keyboard.send_keys("<enter>")
    else:
        printUrl(urlBook[choice])
else:
    exit()


```
## Emoji Speak for chat services such as Discord
- **Author**: [Kreezxil](https://kreezcraft.com)
- **Purpose**: Use emoji to write a sentence, for instance on Discord.
- **Notes**: removed the comment and the if statements, decided to go 100% dictionary lookup method. It is certainly cleaner to look up. It feels a bit faster too.
- **Edited**: 1/28/21 - now even faster!

```python
import time
retCode, phrase = dialog.input_dialog(title='Give me a phrase',message='to make regional?',default='')
lPhrase = phrase.lower()

dictionary = {
    "a":":regional_indicator_a:",
    "b":":regional_indicator_b:",
    "c":":regional_indicator_c:",
    "d":":regional_indicator_d:",
    "e":":regional_indicator_e:",
    "f":":regional_indicator_f:",
    "g":":regional_indicator_g:",
    "h":":regional_indicator_h:",
    "i":":regional_indicator_i:",
    "j":":regional_indicator_j:",
    "k":":regional_indicator_k:",
    "l":":regional_indicator_l:",
    "m":":regional_indicator_m:",
    "n":":regional_indicator_n:",
    "o":":regional_indicator_o:",
    "p":":regional_indicator_p:",
    "q":":regional_indicator_q:",
    "r":":regional_indicator_r:",
    "s":":regional_indicator_s:",
    "t":":regional_indicator_t:",
    "u":":regional_indicator_u:",
    "v":":regional_indicator_v:",
    "w":":regional_indicator_w:",
    "x":":regional_indicator_x:",
    "y":":regional_indicator_y:",
    "z":":regional_indicator_z:",
    "0":":zero:",
    "1":":one:",
    "2":":two:",
    "3":":three:",
    "4":":four:",
    "5":":five:",
    "6":":six:",
    "7":":seven:",
    "8":":eight:",
    "9":":nine:",
    "*":":asterisk:",
    "!":":exclamation:",
    "?":":question:",
    "#":":hash:",
    ".":":small_blue_diamond:"
}

if retCode == 0:
    exit

buildPhrase = ""

for x in lPhrase:
    if  x in dictionary:
        buildPhrase += dictionary[x]
    else:
        buildPhrase += x
    buildPhrase += " "

clipboard.fill_clipboard(buildPhrase)
time.sleep(0.2)
keyboard.send_keys("<ctrl>+v")

``` 
## Coordinate Calculator similar to [Dinnerbone's Coordinate Calculator](https://dinnerbone.com/minecraft/tools/coordinates/)
- **Porting Author**: [Kreezxil](https://kreezcraft.com)
- **Original Author**: [sebkuip](https://github.com/sebkuip)
- **Original Location**: https://github.com/sebkuip/minecraft-region-calculator
- **Purpose**: Takes x y z coordinates and a type for the coordinates given and tells you which region those coordinates are listed in, which chunks they are associated with, and the block range associated with it.
- **Notes**: the regex import might not be needed now.
- **Video**: https://youtu.be/imUh8PCT9f4

```python
import re

def terminate(*args):
    if len(args)>0:
        msg = args[0]
    else:
        msg = "Program Terminated"
    dialog.info_dialog(message=msg)
    exit()

def validate(data):
    try:
        test=int(data)
        return True
    except:
        return False

coordType = ["block","chunk","region"]
coordType.sort()

retCode, chosenType = dialog.list_menu(options=coordType,title="Type",message="Please choose a coordinate type")
if retCode:
    terminate()

retCode, x = dialog.input_dialog(title="X Cord",message="Enter the X coordinate.")
if retCode:
    terminate()
if validate(x)==False:
    terminate("X Coord not a valid integer")

if chosenType=="block":
    retCode, y = dialog.input_dialog(title="Y Coord",message="This coord is pointless, but you may enter it anyways.")
    if retCode:
       terminate()

retCode, z = dialog.input_dialog(title="Z Coord",message="Enter the Z coordinate.")
if retCode:
    terminate()
if validate(z)==False:
    terminate("Z Coord not a valid integer")

utype = chosenType[0]
ux = int(x)
uz = int(z)

title=f"type: {utype} x: {ux} z: {uz}"

if utype == "b":
    msg=f"block {ux},{uz} is inside chunk {ux//16},{uz//16} and within region {ux//512},{uz//512}"

elif utype == "c":
    msg=f"chunk {ux},{uz} contains blocks {ux*16},{uz*16} to {(ux+1)*16-1},{(uz+1)*16-1} and is within region {ux//32},{uz//32}"

elif utype == "r":
    msg=f"region{ux},{uz} contains blocks {ux*512},{uz*512} to {(ux+1)*512-1},{(uz+1)*512-1} and contains chunks {ux*32},{uz*32} to {(ux+1)*32-1},{(uz+1)*32-1}"

dialog.info_dialog(title=title,message=msg)
```
## Autoclicker with toggle using Globals
- **Author**: [Kreezxil](https://kreezcraft.com)
- **Purpose**: clicks where the mouse is at, when the script is run again, it turns off.
```python
x = store.get_global_value("clicker_status")

if x == "on":
    #turn it off if it is on
    store.set_global_value("clicker_status","off")

else:
    #any other value is considered off, should cover nulls
    store.set_global_value("clicker_status","on")

while True:
    time.sleep(0.1)
    mouse.click_relative_self(0,0,1)
    x = store.get_global_value("clicker_status")
    if x == "off":
        #leave the execution if we've been toggled off
        break
```

## Check held keys (workaround!)
Hacky way to check what keys are held down on a device. Uses the `evdev` library which requires additional setup. Check out their readme for more details on installation and what it is capable of. 

https://python-evdev.readthedocs.io/en/latest/

```python
import asyncio
import time
import evdev
from evdev import ecodes as e


async def check_key():
    await asyncio.sleep(1)
    device = evdev.InputDevice('/dev/input/event5')

    if e.KEY_A in device.active_keys():
        print("Key A")


loop = asyncio.new_event_loop()
loop.run_until_complete(check_key())

loop.close()
```

## Date, Time and Window Title stamp. 
Functions in any window, including Windows apps running on Wine.
Sample output of this window: 2021-06-10 04:32 - Editing Scripts contributed 1 · autokey/autokey Wiki — Mozilla Firefox
author: ineuw

```Python

import time

paste_ = "<ctrl>+v"

activetitle_ = window.get_active_title()
ts_ = time.time()
timestamp_ = datetime.datetime.fromtimestamp(ts_).strftime('%Y-%m-%d %H:%M')
combined_ = " " + timestamp_ + " - " + activetitle_
clipboard.fill_clipboard(combined_)
time.sleep(0.1)
keyboard.send_keys(paste_)

```

## Dialog info useful for displaying debugging info

This example creates an info dialog to display the character count of a block of text. Information to be displayed must be in text format.

```Python3

from Xlib import X, display

i = 1
while i < 3:
    clipboard.fill_clipboard("")
    time.sleep(0.1)
    i = i + 1

selectall_ = "<ctrl>+a"
cut_ = "<ctrl>+x"

keyboard.send_keys(selectall_)
time.sleep(0.1)
keyboard.send_keys(cut_)
time.sleep(0.1)
text_ = clipboard.get_clipboard()
time.sleep(0.1)

chars_ = len(text_)
time.sleep(0.1)
chars_ = str(chars_)
time.sleep(0.1)

dialog.info_dialog("length: ", chars_)  

```