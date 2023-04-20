## Contents

* [GUI Dialog That Uses Typed Or Typed-And-Clicked Input](#gui-dialog-that-uses-typed-or-typed-and-clicked-input)
* [GUI Date Dialog](#gui-date-dialog)
* [GUI Date Dialog With Format Control](#gui-date-dialog-with-format-control)
* [Archive URLs using the Wayback Machine](#archive-links-with-the-wayback-machine)


## GUI Dialog That Uses Typed Or Typed-And-Clicked Input
- **Author**: Elliria
- **Purpose**: A GUI dialog that uses typed or a combination of typed and clicked input to launch programs or display dialogs.
- **Notes**: You can customize the script to do pretty much anything you like.

```python
###############################################################
# ABOUT THIS SCRIPT
###############################################################
# A GUI information dialog will be displayed asking for input.
# This script will act on your input.
###############################################################
# USE THIS SCRIPT
###############################################################
# Set a Hotkey for this script (example: Ctrl+K).
# The script will activate when you press Ctrl and K.
# When it prompts you for input, you can choose ONE of these:
    # Press the Esc key to cancel the dialog.
    # ... or ...
    # Click the Cancel button to cancel the dialog.
    # ... or ...
    # Press the Enter key to accept the default example text.
    # ... or ...
    # Click the OK button to accept the default example text.
    # ... or ...
    # Type in some text and press the Enter key.
    # ... or ...
    # Type in some text and click the OK button.
###############################################################
# NOTES
###############################################################
# When using subprocess, remember to use a comma wherever there is a space in a command.
# The subprocess.call function is part of the older high-level API and has been replaced with the subprocess.run function.
# The subprocess.call function waits for the process to complete and provides a return code with its exit status before allowing you to execute other code.
# The subprocess.run function waits for the process to complete and provides a return code with its exit status before allowing you to execute other code.
# The subprocess.Popen function allows you to execute other code and/or interact with the process with the subprocess.communicate function while the process is running.

# Examples of some browsers that could have been used in the script:
    # subprocess.Popen(["C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"])
    # subprocess.Popen(["chrome.exe"])
    # subprocess.Popen(["chromium-browser"])
    # subprocess.Popen(["google-chrome"])
    # subprocess.Popen(["google-chrome-stable"])
###############################################################
# THE SCRIPT
###############################################################
# Message to display to prompt the user for input:
prompt="Please type one of these commands:\n\t* chro\n\t* fire\n\t* goo\n\t* viv\n\t* apple\n\t* banana\n\t* coconut"

# Ask for input, offer a default example, and check the exit code of the command:
retCode, userInput = dialog.input_dialog(title="Input required", message=prompt, default="example")

# If the command was successful (the exit code was zero), take the user's desired action:
if retCode == 0:

    # If chro was typed, open Chromium:
    if userInput == "chro":
        program="chromium-browser"
        subprocess.Popen([program])

    # If fire was typed, open Firefox:
    elif userInput == "fire":
        program="firefox"
        subprocess.Popen([program])

    # If goo was typed, open Google Chrome:
    elif userInput == "goo":
        program="google-chrome"
        subprocess.Popen([program])

    # If viv was typed, open Vivaldi:
    elif userInput == "viv":
        program="vivaldi"
        subprocess.Popen([program])

    # If apple was typed, display a dialog:
    elif userInput == "apple":
        text="You chose apple."
        dialog.info_dialog(title='Info', message=text)

    # If banana was typed, display a dialog:
    elif userInput == "banana":
        text="You chose banana."
        dialog.info_dialog(title='Info', message=text)

    # If apple was typed, display a dialog:
    elif userInput == "coconut":
        text="You chose coconut."
        dialog.info_dialog(title='Info', message=text)

    # If anything else was typed or the default example string was accepted, display an invalid dialog:
    else:
        text = "You typed: " + userInput + "\n\nPlease enter a valid command."
        dialog.info_dialog(title="Invalid", message=text, width="200")

# If the exit code was 1, display a cancel dialog:
elif retCode == 1:
    text = "You pressed the Esc key or the Cancel button."
    dialog.info_dialog(title="Cancelled", message=text, width="200") 

# If the exit code was anything other than 0 or 1, display an error dialog:
else:
    text = "Something went wrong."
    dialog.info_dialog(title="Error", message=text, width="200") 
```


## GUI Date Dialog
- **Author**: Elliria
- **Purpose**: A GUI date-choosing dialog that waits for the user to choose a date and then uses the return code from the dialog to display one of two different dialogs depending on whether the user cancels/closes the window or chooses a date.
- **Notes**: The default format of the date is **YYYY-MM-DD**.

```python
# Create a variable for the return code and the date and put the chosen date's value into the date variable:
retCode, date = dialog.calendar(title="Choose a date")
# Use the following line instead if you'd like to control the format of the date:
# retCode, date = dialog.calendar(title="Choose a date", format="%d-%m-%y")

# If no date is chosen and the Cancel button is clicked, the Esc key is pressed, or the dialog window is closed:
if retCode:
    # Create a message and display it in a dialog:
    myMessage = "No date was chosen."
    dialog.info_dialog(title="Cancelled", message=myMessage, width="200")
else:
    # Display the value of the date variable in a dialog:
    dialog.info_dialog(title="The date you chose is:", message=date, width="200")
```


## GUI Date Dialog With Format Control
- **Author**: Elliria
- **Purpose**: A GUI date-choosing dialog that waits for the user to choose a date and then uses the return code from the dialog to display one of two different dialogs depending on whether the user cancels/closes the window or chooses a date.
- **Notes**: The default format of the date is **YYYY-MM-DD**, but you can use any of these [percent codes](https://help.gnome.org/users/gthumb/stable/gthumb-date-formats.html.en) to control the format. The example below uses ```format="%d-%m-%y"``` to show the date in the **dd-mm-yy** format.

```python
# Create a variable for the return code and the date and put the chosen date's value into the date variable:
retCode, date = dialog.calendar(title="Choose a date", format="%d-%m-%y")

# If no date is chosen and the Cancel button is clicked, the Esc key is pressed, or the dialog window is closed:
if retCode:
    # Create a message and display it in a dialog:
    myMessage = "No date was chosen."
    dialog.info_dialog(title="Cancelled", message=myMessage, width="200")
else:
    # Display the value of the date variable in a dialog:
    dialog.info_dialog(title="The date you chose is:", message=date, width="200")
```
Here's a similar script that gives you format control and pastes the chosen date into the currently-active window:
```python
# Create a variable for the return code and the date and put the chosen date's value into the date variable:
retCode, date = dialog.calendar(title="Choose a date", format="%d-%m-%Y")

# If no date is chosen and the Cancel button is clicked, the Esc key is pressed, or the dialog window is closed:
if retCode:
    # Create a message and display it in a dialog:
    myMessage = "No date was chosen."
    dialog.info_dialog(title="Cancelled", message=myMessage, width="200")
else:
    # Paste the date into the currently-active window:
    keyboard.send_keys(date)
```


## Archive Links with the Wayback Machine
- **Author**: [Anatexis](https://github.com/anatexis)
- **Purpose**: A script that takes a link from the clipboard, archives it using the Wayback Machine, and then places the archived link back in the clipboard as a markdown formatted link as seen here: https://www.flightfromperfection.com/(a).html ([a](https://web.archive.org/web/https://www.flightfromperfection.com/(a).html))
- **Notes**: You can use plain URLs or markdown formatted links. This script uses the requests library to communicate with the Wayback Machine API for archiving and generating archive URLs. It also uses the PyQt5 library for displaying a message box to inform you when the archiving process is complete. Threading is used to make the archiving process non-blocking, allowing the script to continue running while the archiving takes place in the background.
```
###############################################################
# ABOUT THIS SCRIPT
###############################################################
# This script takes a URL from the clipboard, archives it using
# the Wayback Machine, and then replaces the original URL with
# the archived URL in the clipboard. It supports both plain URLs
# and markdown formatted links.
###############################################################
# USE THIS SCRIPT
###############################################################
# Set a Hotkey for this script (example: Ctrl+Shift+L).
# Get a link in your clipboard (copy it with e.g. Ctrl+C)
# The script will activate when you press the assigned hotkey.
# The script will process the copied link, archive it using the 
# Wayback Machine, and replace the link in the clipboard with 
# the archived link in this markdown format:
# ([a](https://web.archive.org/web/https://www.link.com))
###############################################################
# NOTES
###############################################################
# This script uses the requests library to communicate with the
# Wayback Machine API for archiving and generating archive URLs.
# It also uses the PyQt5 library for displaying a message box to
# inform the user when the archiving process is complete.
# Threading is used to make the archiving process non-blocking,
# allowing the script to continue running while the archiving
# takes place in the background.
###############################################################
# THE SCRIPT
###############################################################

import re
import requests
import threading
from PyQt5.QtWidgets import QMessageBox
from typing import Optional, Tuple

def save_web_archive(url: str) -> None:
    save_url = f'https://web.archive.org/save/{url}'
    requests.get(save_url)

def extract_url_from_link(link: str) -> Optional[Tuple[str, str]]:
    markdown_link_pattern = r'\[(.+)\]\((https?://.+)\)'
    plain_link_pattern = r'(https?://.+)'

    if re.match(markdown_link_pattern, link):
        label, url = re.findall(markdown_link_pattern, link)[0]
        return label, url
    elif re.match(plain_link_pattern, link):
        url = re.findall(plain_link_pattern, link)[0]
        return None, url
    else:
        return None

def convert_to_web_archive_url(link: str) -> Optional[str]:
    extracted_data = extract_url_from_link(link)
    if not extracted_data:
        return None

    label, url = extracted_data
    view_url = f'https://web.archive.org/web/{url}'
    threading.Thread(target=save_web_archive, args=(url,)).start()

    return view_url

def main():
    link = clipboard.get_clipboard()
    print(f"Input link: {link}")
    archived_link = convert_to_web_archive_url(link)
    if not archived_link:
        print("Invalid input")
        return

    print(f"Archived link: {archived_link}")

    msg_box = QMessageBox()
    msg_box.setWindowTitle("AutoKey")
    msg_box.setText("Link archived!")
    msg_box.exec_()

    a_link = f"([a]({archived_link}))"
    clipboard.fill_clipboard(a_link)

main()
```
