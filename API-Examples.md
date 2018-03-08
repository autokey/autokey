# API Examples #
Currently there are examples for dialogs. Other types of example to follow.

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
