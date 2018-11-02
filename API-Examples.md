# API Examples #


## Introduction ##

The API examples shown here are for AutoKey-GTK. 

The examples show how to use the various API calls that AutoKey provides. 

The example types are as follows:
- [Clipboard](#clipboard)
- [Dialogs](#dialogs)
- [Keyboard](#keyboard)
- [Mouse](#mouse)
- [Store](#store)
- [System](#system)
- [Window](#window)


## Clipboard ##

- [fill_clipboard](#fill_clipboard)
- [fill_selection](#fill_selection)
- [get_clipboard](#get_clipboard)
- [get_selection](#get_selection)


### fill_clipboard ###

fill_clipboard copies supplied text into the clipboard.

The script does the following:

1. Copies the text 'Hello World' to the clipboard.

2. Waits 0.2 seconds for the clipboard operation to finish. This wait is unlikely to be necessary for small amounts of text, but clipboard operations can be slow.

3. Fetches the text from the clipboard and displays it in an info dialog.


#### fill_clipboard script ####

    import time
    toClip = 'Hello World'
    clipboard.fill_clipboard(toClip)

    time.sleep(0.2)
    fromClip = clipboard.get_clipboard()

    dialog.info_dialog(title='Clipboard contents', 
        message=fromClip, width='200') # width is extra Zenity parameter 


### fill_selection ###

fill_selection copies text into the X selection.

The script does the following:

1. Takes the text 'Hello World' and copies it to the clipboard as the upper case text 'HELLO WORLD'.

2. Waits 0.2 seconds for the clipboard operation to finish. This wait is unlikely to be necessary for small amounts of text, but clipboard operations can be slow.

3. Sends the keys ctrl+v to paste the text from the clipboard.


#### fill_selection script ####

    import time
    cb = 'hello world'
    clipboard.fill_selection(cb.upper())
    time.sleep(0.2)
    keyboard.send_keys('<ctrl>+v')


### get_clipboard ###

The script does the following:

1. Uses get_clipboard to copy the text that is on the clipboard.

2. Waits 0.2 seconds for the clipboard operation to finish. This wait is unlikely to be necessary for small amounts of text, but clipboard operations can be slow.

3. Sends the text the current application as upper case text.


#### get_clipboard script ####

    import time
    cb = clipboard.get_clipboard()
    time.sleep(0.2)
    keyboard.send_keys(cb.upper())


### get_selection ###

The script does the following:

1. Copies the selected text from the current application. If there is an error, the script displays an info dialog that says 'No text selected'.

2. Waits 0.2 seconds for the clipboard operation to finish. This wait is unlikely to be necessary for small amounts of text, but clipboard operations can be slow.

3. Shows the copied text in an info dialog.


#### get_selection script ####

    import time
    try:
        selText = clipboard.get_selection()
        time.sleep(0.2)
        dialog.info_dialog(title='Text from selection', message=selText) 

    except:
        dialog.info_dialog(title='No text selected', 
        message='No text in X selection') 

## Dialogs ##

- [Calendar dialog](#calendar-dialog)
- [Directory Chooser dialog](#directory-chooser-dialog)
- [Information dialog](#information-dialog)
- [Input dialog](#input-dialog)
- [Multiple-selection list menu](#multiple-selection-list-menu)
- [Open File dialog](#open-file-dialog)
- [Password input dialog](#password-input-dialog)
- [Save As dialog](#save-as-dialog)
- [Single-selection list menu](#single-selection-list-menu)


### Calendar dialog ###

The script does the following:

1.  Displays a save as file dialog.

    The dialog returns a tuple that contains the following:

    - An integer value that shows the exit value from the script. This value is 0 for success, an integer for error.

    - A string value that contains the date that was specified on the dialog, using the format YYYY-MM-DD.

2. Displays an information dialog to show one of the following:

   - The error code, if any, from the save as file dialog.

   - The date that was specified on the dialog.


#### Calendar dialog script ####

    retCode, date = dialog.calendar(title='Choose a date')
	if retCode:
		myMessage = 'Dialog exit code was: ' + str(retCode)
		dialog.info_dialog(title='You cancelled the dialog', 
		message=myMessage, 
		width='200')  
                # width is extra zenity parameter. See the zenity manpage for details.
                # this is our fancy faux way of saying:  THIS code BREAKS. it is worthless.


	else:
		dialog.info_dialog(title='The date you chose was', message=date)




### Directory Chooser dialog ###

tuple(int, str) 	
choose_directory(self, title='Select Directory', initialDir='~', **kwargs)


This script does the following:

1.  Displays a directory chooser dialog.

    The dialog returns a tuple that contains the following:

    - An integer value that shows the exit value from the script. This value is 0 for success, an integer for error.

    - A string value that contains the full path of the directory that was specified on the dialog.

2. Displays an information dialog to show one of the following:

   - The error code, if any, from the directory chooser dialog.

   - The full path of the directory that was specified on the dialog.


#### Directory chooser dialog script ####

	retCode, dirName = dialog.choose_directory(title='Choose a directory')

	if retCode:
		myMessage = 'Dialog exit code was: ' + str(retCode)
		dialog.info_dialog(title='You cancelled the dialog', 
		message=myMessage, 
		width='200') # width is extra zenity parameter. See the zenity manpage for details.

	else:
		dialog.info_dialog(title='The directory you chose was', message=dirName)

### Information dialog ###

This script displays an information dialog.


#### Information dialog script ####

	weather = 'Sunny with some showers'
    retCode, user = dialog.info_dialog(title='Weather Forecast', message=weather)
	
	myMessage = retCode + user
	dialog.info_dialog(title='Weather Forecast', message=myMessage)


### Input dialog ###

This script does the following:

1. Displays an input dialog. 

    The Input dialog returns a tuple that contains the following:

	- An integer value that shows the exit value from the script. This value is 0 for success, an integer for error.

	- A string value that contains the text that was entered on the input dialog. 

2. Displays an information dialog to show one of the following:

   - The error code, if any, from the input dialog.

   - The text that was entered on the input dialog.


#### Input dialog script ####

	retCode, userInput = dialog.input_dialog(title='Input required',
		message='Enter a string', 
		default='My string')

	if retCode:
		myMessage = 'Dialog exit code was: ' + str(retCode)
		dialog.info_dialog(title='You cancelled the dialog', 
		message=myMessage, width='200') # width is extra zenity parameter 
	else:
		dialog.info_dialog(title='The string you entered', message=userInput)  # **


### Multiple-selection list menu ###

This script does the following:

1.  Displays a multiple-selection list. 

    The multiple-selection list returns a tuple that contains the following:

    - An integer value that shows the exit value from the script. This value is 0 for success, an integer for error.

    - A list of string values, each one of which is the text of an option that was selected on the dialog.

2. Displays an information dialog to show one of the following:

   - The error code, if any, from the multiple-selection list.

   - A list that contains the text of each item that was selected on the multiple-selection list.


#### Multiple-selection list script ####

	optionShapes = ['Square', 'Triangle', 'Rectangle']

	retCode, choices = dialog.list_menu_multi(options=optionShapes, 
		title='Choose all shapes that have four sides', 
		message='Shapes',
		defaults='Square,Rectangle', 
		height='250') # height is extra zenity parameter. See the zenity manpage for details.

	if retCode:
		myMessage = 'Dialog exit code was: ' + str(retCode)

		dialog.info_dialog(title='You cancelled the dialog', 
		message=myMessage, 
		width='200')  # width is extra zenity parameter. See the zenity manpage for details.

	else:
		myMessage = ''
		for item in choices:
			myMessage = myMessage + '\n' + item

		dialog.info_dialog(title='Your choice was', message=myMessage)


### Open File dialog ###

This script does the following:

1.  Displays an open file dialog.

    The dialog returns a tuple that contains the following:

    - An integer value that shows the exit value from the script. This value is 0 for success, an integer for error.

    - A string value that contains the full path of the file that was specified on the dialog.

2. Displays an information dialog to show one of the following:

   - The error code, if any, from the open file dialog.

   - The full path of the file that was specified on the dialog.


#### Open file dialog script ####

	retCode, fName = dialog.open_file(title='Open File')

	if retCode:
		myMessage = 'Dialog exit code was: ' + str(retCode)
		dialog.info_dialog(title='You cancelled the dialog', 
		message=myMessage, 
		width='200')  # width is extra zenity parameter. See the zenity manpage for details.

	else:
		dialog.info_dialog(title='The file you chose was', message=fName)


### Password input dialog ###

This script does the following:

1.  Displays a password input dialog. 

    The password input dialog returns a tuple that contains the following:

    - An integer value that shows the exit value from the script. This value is 0 for success, an integer for error.

    - A string value that contains the plain text password that was entered on the dialog.

2. Displays an information dialog to show one of the following:

   - The error code, if any, from the password input dialog.

   - The password that was entered on the password input dialog.


#### Password dialog script ####

	retCode, pwd = dialog.password_dialog(title='Enter password', message='Enter password')

	if retCode:
		myMessage = 'Dialog exit code was: ' + str(retCode)
		dialog.info_dialog(title='You cancelled the dialog', 
		message=myMessage, width='200') # width is extra Zenity parameter 
	else:
		dialog.info_dialog(title='The password you entered', message=pwd)


### Save As dialog ###

This script does the following:

1.  Displays a save as file dialog.

    The dialog returns a tuple that contains the following:

    - An integer value that shows the exit value from the script. This value is 0 for success, an integer for error.

    - A string value that contains the full path of the file that was specified on the dialog.

2. Displays an information dialog to show one of the following:

   - The error code, if any, from the save as file dialog.

   - The full path of the file that was specified on the dialog.

#### Save As dialog script ####


	retCode, fName = dialog.open_file(title='Save As')

	if retCode:
		myMessage = 'Dialog exit code was: ' + str(retCode)
		dialog.info_dialog(title='You cancelled the dialog', 
		message=myMessage, 
		width='200') # width is extra zenity parameter. See the zenity manpage for details.

	else:
		dialog.info_dialog(title='You chose to save file', message=fName)


### Single-selection list menu ###

This script does the following:

1.  Displays a single-selection list. 

    The single-selection list menu returns a tuple that contains the following:

    - An integer value that shows the exit value from the script. This value is 0 for success, an integer for error.

    - A string value that contains the text of the selection from the dialog.

2. Displays an information dialog to show one of the following:

   - The error code, if any, from the single-selection list.

   - The text of the item that was selected on the single-selection list.


#### Single-selection list script ####

	optionColours = ['Blue', 'Red', 'Green', 'Yellow']

	retCode, choice = dialog.list_menu(options=optionColours, 
		title='Choose your favourite colour', 
		message='Colours', 
		default=None,
		width='200',  # width is an extra zenity parameter. See the zenity manpage for details.
		height='250') # height is an extra zenity parameter. See the zenity manpage for details.

	if retCode:
		myMessage = 'Dialog exit code was: ' + str(retCode)
		dialog.info_dialog(title='You cancelled the dialog', 
		message=myMessage, 
		width='200')  # width is an extra zenity parameter. See the zenity manpage for details.

	else:
		dialog.info_dialog(title='Your choice was', message=choice)



  	
## Keyboard ##
	
- [Fake key press](#fake-key-press)	
- [Press key](#press-key)	
- [Release key](#releases-key)	
- [Send key](#send-key)	
- [Send keys](#send-keys)	
- [Wait for key press](#wait-for-key-press)	




### Fake key press ###

Fake key presses can be useful to send key presses if an application does not respond to [Send key](#send-key).

This script sends '\<down>' five times.



#### Fake key press script ####

    keyboard.fake_keypress('<down>', repeat=5**)


### Press key ###

**press_key** makes AutoKey hold down a key until it is specifically released. 

This script presses \<ctrl>, then sends 'd' five times, and then releases \<ctrl>.

See [Release key](#release-key)

#### Press key script ####


    keyboard.press_key('<ctrl>')
    keyboard.send_keys('d', repeat=5)
    keyboard.release_key('<ctrl>')


### Release key ###

**release_key** releases a key that has previously been pressed by **press_key**.

See [Press_key](#press-key)

#### Release key script ####

    keyboard.press_key('<ctrl>')
    keyboard.fake_keypress('d', repeat=5)
    keyboard.release_key('<ctrl>')

### Send key ###

**send_key** sends a single keystroke one or more times.

The script sends 'z' three times.

send_key sends a single keystroke. You cannot use send_key on its own to send
keys that are modified with Crtl, Shift, or Alt, for example. 

If you want to use modifiers, use either [send_keys](#send-keys) or [press_key](#press-key).


#### Send key script ####

    keyboard.send_key('z',repeat=3)

### Send keys ###

**send_keys** sends a sequence of keystrokes.

The scripts sends 'Hello World!'.

### Send keys ###

    keyboard.send_keys('Hello World!')


### Wait for key press ###

This script does the following:

1.  Waits for the user to press \<ctrl>+d.

    The function returns a boolean.

2. Displays an information dialog to show one of the following:

   - The error code, if any, from the **wait_for_keypress** function.

   - A message to say that you have pressed \<ctrl>+d.

You cannot use this function to wait for modifier keys, such as \<ctrl>, on their own


#### Wait for key press script ####

	retCode = keyboard.wait_for_keypress('d',modifiers=['<ctrl>'],timeOut=5)

	if retCode:
		myMessage = 'Wait for keypress exit code was: ' + str(retCode)
		dialog.info_dialog(title='You pressed <ctrl>+d', 
		message=myMessage, 
		width='200') # width is extra Zenity parameter.  See the zenity manpage for details.
	else:
		myMessage = 'Wait for keypress exit code was: ' + str(retCode)
		dialog.info_dialog(title='Timeout', message=myMessage)


## Mouse ##

- [Click_absolute](#click_absolute)
- [Click_relative](#click_relative)
- [Click_relative_self](#click_relative_self)
- [Wait_for_click](#wait_for_click)


### Click_absolute ###

click_absolute sends a mouse click relative to the whole screen.

The script clicks the left mouse button at position x=200, y=300 relative to the screen.


#### Click_absolute script ####

    # mouse buttons: left=1, middle=2, right=3
    mouse.click_absolute(200, 300, 1)


### Click_relative ###

click_relative sends a mouse click relative to the active window.

The script clicks the left mouse button at position x=200, y=300 on the current window.

#### Click_relative script ####

    # mouse buttons: left=1, middle=2, right=3
    mouse.click_relative(200, 300, 1)


### Click_relative_self ###

click_relative sends a mouse click relative to the current mouse cursor position.

The script waits for 4 seconds and then clicks the left mouse button at position x=100, y=150 relative to the current mouse cursor position.

#### Click_relative_self script ####

    import time
    time.sleep(4)
    # mouse buttons: left=1, middle=2, right=3
    mouse.click_relative_self(100, 150, 1)


### Wait_for_click ###

wait_for_click waits for a mouse button to be clicked. You specify which mouse button to wait for and the maximum time to wait.

The script waits for a maximum of 10 seconds for a left click. When the click is detected the script displays a dialog.


#### Wait_for_click script ####

    # mouse buttons: left=1, middle=2, right=3
    mouse.wait_for_click(1, timeOut=10)
    dialog.info_dialog(title='Click detected', message='You clicked the left button')






## Store ##

- [Get global value](#get-global-value)
- [Get value](#get-value)
- [Remove global value](#remove-global-value)
- [Remove value](#remove-value)
- [Set global value](#set-global-value)
- [Set value](#set-value)


### Get global value ###

This script sets global value "myValue" to "hello" and then gets the value that has been set and displays it in an info dialog.

Global values can be accessed by all AutoKey scripts. The values are available in future AutoKey sessions.


#### Get global value script ####

    store.set_global_value("myValue","hello")
    x = store.get_global_value("myValue")
    dialog.info_dialog(title='Value of global value myValue', 
        message=x, width='200') 


### Get value ###

This script sets local value "myLocalValue" to "My local value" and then gets the value that has been set and displays it in an info dialog.

Local script variables can be accessed only by the script that wrote them. The values are available in future AutoKey sessions.

Script variables can be accessed only by the script that wrote them. The values are available in future AutoKey sessions.

#### Get value script ####

    store.set_value("myValue","hello")
    x = store.get_value("myValue")
    dialog.info_dialog(title='Value of local value myValue', 
        message=x, width='200') 


### Remove global value ###

This script does the following:

1. Sets global value "myValue" to "hello" 

2. Gets the value that has been set and displays it in an info dialog

3. Removes global value "myValue"

4. Attempts to get the value of "myValue", but fails because "myValue" no longer exists.


#### Remove global value script ####

    store.set_global_value("myValue","hello")
    x = store.get_global_value("myValue")

    dialog.info_dialog(title='Value of global value myValue', 
        message=x, width='200') # width is extra Zenity parameter 

    store.remove_global_value("myValue")

    try:
        y = store.get_global_value("myValue")
        dialog.info_dialog(title='Value of global value myValue', 
            message=y, width='200') # width is extra Zenity parameter 

    except TypeError:
        dialog.info_dialog(title='Global value myValue', 
            message="myValue does not exist", width='200') # width is extra Zenity parameter 


### Remove value ###

This script does the following:

1. Sets local value "myValue" to "hello" 

2. Gets the value that has been set and displays it in an info dialog

3. Removes local value "myValue"

4. Attempts to get the value of "myValue", but fails because "myValue" no longer exists.


#### Remove value script ####

    store.set_value("myValue","hello")
    x = store.get_value("myValue")

    dialog.info_dialog(title='Value of local value myValue', 
        message=x, width='200') # width is extra Zenity parameter 

    store.remove_value("myValue")

    try:
        y = store.get_value("myValue")
        dialog.info_dialog(title='Value of local value myValue', 
            message=y, width='200') # width is extra Zenity parameter 

    except TypeError:
        dialog.info_dialog(title='Local value myValue', 
            message="myValue does not exist", width='200') # width is extra Zenity parameter 




### Set global value ###

This script sets global value "myValue" to "hello" and then gets the value that has been set and displays it in an info dialog.


#### Set global value script ####
    
    store.set_global_value("myValue","hello")
    x = store.get_global_value("myValue")
    dialog.info_dialog(title='Value of global value myValue', 
        message=x, width='200') 


### Set value ###

This script sets local value "myLocalValue" to "My local value" and then gets the value that has been set and displays it in an info dialog.

Local script variables can be accessed only by the script that wrote them. The values are available in future AutoKey sessions.


#### Set value script ####

    store.set_value("myValue","hello")
    x = store.get_value("myValue")
    dialog.info_dialog(title='Value of local value myValue', 
        message=x, width='200') 



## System ##

- [Create_file](#create_file)
- [Exec_command](#exec_command)


### Create_file ###

create_file creates a file in the file system with the specified contents, if any.

The script creates file /tmp/myFile.txt with the contents "Hello World".


#### Create_file script ####

    system.create_file('/tmp/myFile.txt', contents='Hello World')


### Exec_command ###

exec_command executes a system command.

The script executes the command 'ls /tmp' and captures the output. The script then saves the listing to file '/tmp/myListing.txt'.

#### Exec_command script ####

    output = system.exec_command('ls /tmp/', getOutput=True)
    system.create_file('/tmp/myListing.txt', contents=output)





## Window ##

- [Get class of active window](#get-class-of-active-window)
- [Get title of active window](#get-title-of-active-window)
- [Get window geometry](#get-window-geometry)
- [Move window to different desktop](#move-window-to-different-desktop)
- [Resize or move window](#resize-or-move-window) 
- [Set window property](#set-window-property)
- [Switch to different desktop](#switch-to-different-desktop)
- [Wait for window to exist](#wait-for-window-to-exist)
- [Wait for window to have focus](#wait-for-window-to-have-focus)


	
### Get class of active window ###

This script gets the class of the active window and then displays it in an info dialog.


#### Get class of active window script ####

	winClass = window.get_active_class()
	dialog.info_dialog(title='Window class', message=winClass)


###  Get title of active window ###

This script gets the title of the active window and then displays it in an info dialog.


#### Get title of active window script ####

	winTitle = window.get_active_title()
	dialog.info_dialog(title='Window title', message=winTitle)


### Get window geometry ###

This script gets the geometry of the active window and then displays an info dialog that shows the values.


#### Get window geometry script ####

	winGeometry = 'X-origin: %s\nY-origin: %s\nWidth: %s\nHeight: %s'  %(winXOrigin, winYOrigin, winWidth, winHeight)
	dialog.info_dialog(title='Window geometry', message=winGeometry)


### Move window to different desktop ###

This script moves the 'Unsaved Document' window to desktop three.


#### Move window to different desktop script ####

	window.move_to_desktop('Unsaved Document', 3, matchClass=False) # desktop number is an integer. The first desktop is 0.


### Set window property ###

This script maximizes horizontally the 'Unsaved Document' window.


#### Set window property script ####

	window.set_property('Unsaved Document', 'add','maximized_horz', matchClass=False)


### Switch to different desktop ###

This script switches focus to desktop two.


#### Switch to different desktop script ####

	window.switch_desktop(2) # The first desktop is 0.


### Wait for window to exist ###

This script waits up to five seconds for a specified window to exist and then displays an info dialog that shows the exit code.

The exit code is **True*** if the window has focus, **False** if the script times out.

#### Wait for window to exist script ####

	retCode = window.wait_for_exist('Unsaved Document', timeOut=5)
	myMessage = 'Exit code was: ' + str(retCode)
	dialog.info_dialog(title='Exit code', message=myMessage)


### Wait for window to have focus ###

This script waits five seconds for the Thunderbird window to have focus and then displays an info dialog that shows the exit code. 

The exit code is **True** if the window has focus, **False** if the script times out.


#### Wait for window to have focus script ####

	retCode = window.wait_for_focus('.*Thunderbird', timeOut=5)
	myMessage = 'Exit code was: ' + str(retCode)
	dialog.info_dialog(title='Exit code', message=myMessage)


### Resize or move window ###

This script resizes the 'Unsaved Document' window.


#### Resize or move window script ####

	window.resize_move('Unsaved Document', xOrigin=20, yOrigin=20, width=200, height=200, matchClass=False)
