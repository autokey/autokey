
## Contents

* [Introduction](#introduction)
* [Display the Active Front End](#display-the-active-front-end)
* [Display Active Window Information](#display-active-window-information)
* [Test for the Active Front End](#test-for-the-active-front-end)
* [Using Dates in Scripts](#using-dates-in-scripts)
* [List Menu](#list-menu)
* [X Selection](#x-selection)
* [Persistent Value](#persistent-value)
* [Create new abbreviation](#create-new-abbreviation)
* [Create new phrase](#create-new-phrase)
* [Start external scripts](#start-external-scripts)


## Introduction 
This page contains example scripts to demonstrate the **basic** capabilities of AutoKey's scripting service.

Feel free to use these scripts for your own purposes. However, if you significantly modify them or come up with something new as a result of using them, please post them in [one of our community platforms](https://github.com/autokey/autokey/wiki/Community) so one of the wiki moderators can add them here for all to benefit.

All submitted scripts are publicly licensed as [GNU GPL v3](http://www.gnu.org/licenses/gpl.html)

For specific details on the custom functions available to AutoKey scripts, see the [API reference](https://autokey.github.io).

## Display the Active Front End

Display the AutoKey front end (GTK or Qt) you are currently using:
```python
# Run a system command to check for the full name of the current AutoKey process name and store it in a variable:
process_name = system.exec_command("ps -q $(pgrep autokey) -o comm=")

# If gtk is in the process name:
if "gtk" in process_name:
    # Display the specified dialog:
    dialog.info_dialog(message="You are using the GTK front-end")
# If qt is in the process name:
elif "qt" in process_name:
    # Display the specified dialog:
    dialog.info_dialog(message="You are using the Qt front-end.")
# If anything else happens:
else:
    # Do nothing:
    pass
```
## Display Active Window Information

Display the information of the active window after 2 seconds:
```python
    import time
    time.sleep(2)
    winTitle = window.get_active_title()
    winClass = window.get_active_class()
    dialog.info_dialog("Window information", "Active window information:\\nTitle: '%s'\\nClass: '%s'" % (winTitle, winClass))
```
## Test for the Active Front End
Test for the AutoKey front end (GTK or Qt) you are currently using and store the result in the **result** variable.

```python
# Create a function to test whether the GTK or Qt front-end is currently in use:
def test():
    # Run a system command to get the full name of the current AutoKey process and store it in a variable:
    process_name = system.exec_command("ps -q $(pgrep autokey) -o comm=")
    # If gtk is in the process name:
    if "gtk" in process_name:
        # Return the specified Boolean value: 
        return True
    # If qt is in the process name:
    else:
        # Return the specified Boolean value: 
        return False
# Run the function and store the result in a variable:
result = test()
```
## Using Dates in Scripts

Users frequently need to use the date or time in a script.

The easiest way to get and process a date is by using the Python **time** or **datetime** modules:
```python
    import time
    output = time.strftime("date %Y:%m:%d")
    keyboard.send_keys(output)
```
If you need a specific time other than "now", Python will be happy to oblige, but setting that up is a separate (purely Python) topic with many options (see links at the end).

You can also do things like run the system date command.

This script uses the simplified ```system.exec_command()``` function to execute the Unix **date** program, get the output, and send it via keyboard output:
```python
    output = system.exec_command("date")
    keyboard.send_keys(output)
```
or, with more options:
```python
    commandstr="date "+%Y-%m-%d" --date="next sun""
    output = system.exec_command(commandstr)
    keyboard.send_keys(output)
```
but this creates another process and makes your script dependent on the behavior of the external command with respect to both its output format and any error conditions it may generate.

### Background

Time itself is stored in binary format (from ```man clock_gettime(3)```):

           All  implementations  support  the system-wide real-time clock, which is identified by CLOCK_REALTIME.  Its time represents
           seconds and nanoseconds since the Epoch.

Since this is essentially a really big integer, it is a handy form to use for calculations involving time. The Linux **date** command (and the Python ```strftime()``` function) understands this format and will happily convert from and to various other formats - probably using the same or a very similar **strftime** utility.

See [datetime](https://docs.python.org/3/library/datetime.html) and [time](https://docs.python.org/3/library/time.html#module-time) for all the gory details.

## List Menu

This script shows a simple list menu, grabs the chosen option, and sends it via keyboard output:
```python
    choices = ["something", "something else", "a third thing"]
    retCode, choice = dialog.list_menu(choices)
    if retCode == 0:
        keyboard.send_keys("You chose " + choice)
```
## X Selection

This script grabs the current mouse selection, erases it, and then inserts it again as part of a phrase:
```python
    text = clipboard.get_selection()
    keyboard.send_key("<delete>")
    keyboard.send_keys("The text %s was here previously" % text)
```
## Persistent Value

This script demonstrates 'remembering' a value in the store between separate invocations of the script:
```python
    if not store.has_key("runs"):
        # Create the value on the first run of the script
        store.set_value("runs", 1)
    else:
        # Otherwise, get the current value and increment it
        cur = store.get_value("runs")
        store.set_value("runs", cur + 1)

        keyboard.send_keys("I've been run %d times!" % store.get_value("runs")) ```
```
## Create new abbreviation

This script creates a new phrase with an associated abbreviation from the current contents of the X mouse selection (although you could easily change it to use the clipboard instead by using ```clipboard.get_clipboard()```):
```python
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
```
## Create new phrase

This is similar to the above script, but creates the phrase without an abbreviation:
```python
    # The sleep seems to be necessary to avoid lockups
    import time time.sleep(0.25)

    contents = clipboard.get_selection()
    if len(contents) > 20:
        title = contents[0:17] + "..."
    else:
        title = contents
    folder = engine.get_folder("My Phrases")
    engine.create_phrase(folder, title, contents)
```
## Start external scripts

In case you've got some Bash scripts or want to start a program with a shortcut:

To start a script:
```python
    import subprocess
    subprocess.Popen(["/bin/bash", "/home/foobar/bin/startfooscript.sh"])
```
To start a program with Wine:
```python
    import subprocess
    subprocess.Popen(["wine", "/home/foobar/wine/program/some.exe"])
```
