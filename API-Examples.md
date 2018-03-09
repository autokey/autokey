# API Examples #
Currently there are examples for dialogs and windows. Other types of example to follow.

- [Dialogs](#dialogs)
- [Window](#window)

# Dialogs #

- [Information dialog](#information-dialog)
- [Input dialog](#input-dialog)
- [Password input dialog](#password-input-dialog)
- [Single-selection list menu](#single-selection-list-menu)
- [Multiple-selection list menu](#multiple-selection-list-menu)
- [Open File dialog](#open-file-dialog)
- [Save As dialog](#save-as-dialog)
- [Directory Chooser dialog](#directory-chooser-dialog)


## Introduction ##

The API examples shown here are for AutoKey-GTK. 

The examples show how to use the various API calls that AutoKey provides. 


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
		dialog.info_dialog(title='The string you entered', message=userInput**


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

### Calendar dialog ###

This script does the following:

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
		width='200')  # width is extra zenity parameter. See the zenity manpage for details.
	else:
		dialog.info_dialog(title='The date you chose was', message=date)




# Window #

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


