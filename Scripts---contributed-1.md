## Get a Gmail URL from the 'Open In New Window' button

If you use the 'preview pane' view in Gmail, you will note that you cannot then see the URLs of individual messages in the address bar. Yet each message does indeed have an unique URL. To get the URL of a message without having to switch to the standard view:

* click on the 'Open In New Window' button at the top right of the message preview pane ([image](https://plus.google.com/+Gmail/posts/hvVnBaQMTfj))
* in the popup, click once in the address bar to select the URL
* run the script below (I run it from the Autokey system tray menu)
* the correct URL replace the popup's URL in your clipboard

script:
```python
import re
url = clipboard.get_selection()
gmail_baseurl="https://mail.google.com/mail/u/0/#inbox/"
match = re.search(r'(?<=th=)(\w+)(&)', url)
clipboard.fill_clipboard(gmail_baseurl + match.group(1))
```

## Convert text case to lowercase and replace spaces with hyphens
This is useful for converting the name of a GitHub Issue into a string that's suitable for a Git branch, if you follow the style of 'named-branch' Git development.

For example:

> Unexpected Window title: FocusProxy

is returned as

> unexpected-window-title:-focusproxy

script:
```python
text = clipboard.get_selection()
clipboard.fill_clipboard(text.lower().replace(' ', '-'))
```

## Automatically collect and paste information about the current platform
Useful for making bug reports especially on web applications where the platform and browser version may be relevant.

example:

> Platform: Linux-4.13.0-37-generic-x86_64-with-LinuxMint-18.3-sylvia  
> Browser: Google Chrome 65.0.3325.181  
> Browser: Mozilla Firefox 59.0.1  
> Date Tested :Wed 28 Mar 14:46:48 BST 2018  

script:
```python
import platform
output = ""
output += "Platform: " + platform.platform() + "\n"
output += "Browser: " + os.popen("google-chrome --version").read()
output += "Browser: " + os.popen("firefox --version").read()
output += "Date Tested :" + system.exec_command("date")
keyboard.send_keys(output)
```

## Insert current DateTime in the format YYYY.MM.DD HH:MM:SS
example:
> 2018.04.23 23:47:00 

script:
```python
from datetime import datetime
keyboard.send_keys(datetime.now().strftime('%Y.%m.%d %H:%M:%S'))
```

## Insert current Time in the format HH:MM:SS
example:
> 23:47:00 

script:
```python
from datetime import datetime
keyboard.send_keys(datetime.now().strftime('%H:%M:%S'))
```

## Insert current Date only in the format YYYY.MM.DD
example:
> 2018.04.23

script:
```python
from datetime import datetime
keyboard.send_keys(datetime.now().strftime('%Y.%m.%d'))
```

## Search for text from your clipboard in your Browser

script:
```python
import  webbrowser
import time

time.sleep(0.1)
webbrowser.open("http://www.google.de/search?q="+clipboard.get_clipboard())
```

## open a certain website:

script:
```python
import webbrowser
import time

time.sleep(0.1)
site = "youtube.com"
webbrowser.get('google-chrome').open_new_tab(site)
# webbrowser.get('firefox').open_new(site) # in case you want to open a new site in firefox
# webbrowser.get('firefox').open_new_tab(site)
```

## Unpack all zipped files from the Download folder and delete the zip file afterwards.
Author: [kolibril13](https://github.com/kolibril13)
script:
```py
import os, zipfile, subprocess
from pathlib import Path

path = Path.home() / "Downloads"
dir_name = str(path) + "/"
extension = ".zip"
file_to_delete = 'checklist.csv' # assuming there is one file "checklist.csv" that one does not want to have in the unpacked folder.
os.chdir(dir_name)  # change directory from working dir to dir with files

for item in os.listdir(dir_name):  # loop through items in dir
    if item.endswith(extension):  # check for ".zip" extension
        item_name=item[:-4]
        file_name = os.path.abspath(item)  # get full path of files
        zip_ref = zipfile.ZipFile(file_name)  # create zipfile object
        zip_ref.extractall(dir_name + item_name)  # extract file to dir
        print(os.listdir(dir_name + item_name + '/'))
        if file_to_delete in os.listdir(dir_name + item_name + '/'):  # deletes 'checklist.csv'
            os.remove(dir_name + item_name + '/' + file_to_delete)
        zip_ref.close()  # close file
        os.remove(file_name)  # delete zipped file
        subprocess.Popen(['xdg-open', dir_name + item_name + '/'])
```

## Reduce image qualities in a certain folder
Author: [kolibril13](https://github.com/kolibril13)
script:
```python

from pathlib import Path
import os
suffix = ".jpg"
input_path= Path.home() / "Downloads"
file_paths= [subp for subp in input_path.rglob('*') if  suffix == subp.suffix]
file_paths.sort()

output_path =  Path.home() / "Downloads/processed"
output_path.mkdir(parents=True, exist_ok=True)


for file_p in file_paths:
	input = str(file_p)
	output = str(  output_path / file_p.name  ) 
	command = f"ffmpeg -i {input} -q:v 10 {output}"
	os.system(command)
```

## Make a screenshot and move it to the downloads folder in case that a name is given, otherwise move it to the clipboard.
Author: [kolibril13](https://github.com/kolibril13)
script:
```py
# requires:
# * sudo apt-get install gnome-screenshot
# * sudo apt-get install xclip 


import time
import os

working_directory = "~/Downloads/"

command = "gnome-screenshot -a  -f '/tmp/temp.png' "
os.system(command)

name = dialog.input_dialog(title='', message='Screenshot name:', default='').data

from_path = '/tmp/temp.png'
if name == "" :
    os.system("xclip -selection clipboard -t image/png -i /tmp/temp.png")
    
else:
    to_path = working_directory + name + '.png'
    command2 = "mv " + from_path + " " + to_path
    os.system(command2)
```

## Ping or TracePath Mojang Minecraft Services Servers
Author: [Kreezxil](https://kreezcraft.com)

While this could've been done easier in a shell script I thought it would be fun to do it in Autokey. The script contains an array of Mojang servers that can cause issues for players if they are down. There is an action array too so you can see how to easily add more actions. 

Each time you trigger it the script will have you choose which server you would like to perform an action on, it defaults to all. Then it will ask you what action you would like to perform on what you just chose in the server section, this will default to `ping -c 1`.

```python
from autokey.common import USING_QT

mjservers = []
mjservers.append(["all","default"])
mjservers.append(["minecraft.net"])
mjservers.append(["account.mojang.com"])
mjservers.append(["authserver.mojang.com"])
mjservers.append(["sessionserver.mojang.com"])
mjservers.append(["skins.minecraft.net"])
mjservers.append(["textures.minecraft.net"])

mjactions = []
mjactions.append(["ping -c 1","default"])
mjactions.append(["ping -c 10"])
mjactions.append(["tracepath"])

menuBuilder = []
defEntry = ""
menuEntry = "{}"
for x in mjservers:
  entry=menuEntry.format(x[0])
  if x.count("default") == 1:
      defEntry=entry
  menuBuilder.append(entry)

# We use the boolean check to see which toolkit we're using
# the different toolkits receive extra parameters differently
if USING_QT:
    retCode, choice = dialog.list_menu(menuBuilder, title="Which server?", default=defEntry)
else:
    retCode, choice = dialog.list_menu(menuBuilder, title="Which server?", height='800',width='350',default=defEntry)

if retCode:
    #message canceled, tortue ended
    exit()
else:
    selection="{}"
    server=selection.format(
        mjservers[
            menuBuilder.index(choice)
        ][0]
    )
        
menuBuilder = []
defEntry = ""
menuEntry = "{}"
for x in mjactions:
  entry=menuEntry.format(x[0])
  if x.count("default") == 1:
      defEntry=entry
  menuBuilder.append(entry)

# We use the boolean check to see which toolkit we're using
# the different toolkits receive extra parameters differently
if USING_QT:
    retCode, choice = dialog.list_menu(menuBuilder, title="Which action?", default=defEntry)
else:
    retCode, choice = dialog.list_menu(menuBuilder, title="Which action?", height='800',width='350',default=defEntry)

if retCode:
    exit()
else:
    selection="{}"
    action=selection.format(
        mjactions[
            menuBuilder.index(choice)
        ][0]
    )
        
if server == "all":
    for x in mjservers:
        thisbethat="{} {}"
        if x[0] != "all":
            keyboard.send_keys(thisbethat.format(action,x[0]))
            keyboard.send_key("<enter>")
else:
    thisbethat="{} {}"
    keyboard.send_keys(thisbethat.format(action,server))
    keyboard.send_key("<enter>")
```

````Python
## Date, Time and Window Title stamp. Functions in any window, including Windows apps running on Wine.
sample output of this window: 2021-06-10 04:32 - Editing Scripts contributed 1 · autokey/autokey Wiki — Mozilla Firefox
author: ineuw

import time

paste_ = "<ctrl>+v"

activetitle_ = window.get_active_title()
ts_ = time.time()
timestamp_ = datetime.datetime.fromtimestamp(ts_).strftime('%Y-%m-%d %H:%M')
combined_ = " " + timestamp_ + " - " + activetitle_
clipboard.fill_clipboard(combined_)
time.sleep(0.1)
keyboard.send_keys(paste_)
