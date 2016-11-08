Introduction

This page contains some very basic script examples to demonstrate the capabilities of AutoKey's scripting service.

For specific details on the custom functions available to AutoKey scripts, see the API reference.

Scripts

Display Active Window Information

Displays the information of the active window after 2 seconds

import time time.sleep(2) winTitle = window.get_active_title() winClass = window.get_active_class() dialog.info_dialog("Window information", "Active window information:\\nTitle: '%s'\\nClass: '%s'" % (winTitle, winClass))

Insert Current Date/Time

This script uses the simplified system.exec_command() function to execute the Unix date program, get the output, and send it via keyboard output

output = system.exec_command("date") keyboard.send_keys(output)

List Menu

This script shows a simple list menu, grabs the chosen option and sends it via keyboard output.

``` choices = ["something", "something else", "a third thing"]

retCode, choice = dialog.list_menu(choices) if retCode == 0: keyboard.send_keys("You chose " + choice) ```

X Selection

This script grabs the current mouse selection, then erases it, and inserts it again as part of a phrase.

text = clipboard.get_selection() keyboard.send_key("<delete>") keyboard.send_keys("The text %s was here previously" % text)

Persistent Value

This script demonstrates 'remembering' a value in the store between separate invocations of the script.

``` if not store.has_key("runs"): # Create the value on the first run of the script store.set_value("runs", 1) else: # Otherwise, get the current value and increment it cur = store.get_value("runs") store.set_value("runs", cur + 1)

keyboard.send_keys("I've been run %d times!" % store.get_value("runs")) ```

Create new abbreviation

This script creates a new phrase with an associated abbreviation from the current contents of the X mouse selection (although you could easily change it to use the clipboard instead by using clipboard.get_clipboard()).

``` import time time.sleep(0.25)

The sleep seems to be necessary to avoid lockups

contents = clipboard.get_selection() retCode, abbr = dialog.input_dialog("New Abbreviation", "Choose an abbreviation for the new phrase") if retCode == 0: if len(contents) > 20: title = contents[0:17] + "..." else: title = contents folder = engine.get_folder("My Phrases") engine.create_abbreviation(folder, title, abbr, contents) ```

Create new phrase

This is similar to the above script, but just creates the phrase without an abbreviation.

``` import time time.sleep(0.25)

The sleep seems to be necessary to avoid lockups

contents = clipboard.get_selection() if len(contents) > 20: title = contents[0:17] + "..." else: title = contents folder = engine.get_folder("My Phrases") engine.create_phrase(folder, title, contents) ```