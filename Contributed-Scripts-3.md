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
		browser="chromium-browser"
		subprocess.Popen([browser])

	# If fire was typed, open Firefox:
	elif userInput == "fire":
		browser="firefox"
		subprocess.Popen([browser])

	# If goo was typed, open Google Chrome:
	elif userInput == "goo":
		browser="google-chrome"
		subprocess.Popen([browser])

	# If viv was typed, open Vivaldi:
	elif userInput == "viv":
		browser="vivaldi"
		subprocess.Popen([browser])

	# If apple was typed, display a dialog:
	elif userInput == "apple":
		dialog.info_dialog(title='Info', message="You chose apple.")

	# If banana was typed, display a dialog:
	elif userInput == "banana":
		dialog.info_dialog(title='Info', message="You chose banana.")

	# If apple was typed, display a dialog:
	elif userInput == "coconut":
		dialog.info_dialog(title='Info', message="You chose coconut.")

	# If anything else was typed or the default example string was accepted, display an invalid dialog:
	else:
		invalid = "You typed: " + userInput + "\n\nPlease enter a valid command."
		dialog.info_dialog(title="Invalid", message=invalid, width="200")

# If the exit code was 1, display a cancel dialog:
elif retCode == 1:
	cancelled = "You pressed the Esc key or the Cancel button."
	dialog.info_dialog(title="Cancelled", message=cancelled, width="200") 

# If the exit code was anything other than 0 or 1, display an error dialog:
else:
	error = "Something went wrong."
	dialog.info_dialog(title="Error", message=error, width="200") 
```
