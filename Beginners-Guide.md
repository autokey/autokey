This page contains a basic introduction on what AutoKey is and what it does.

## Glossary of AutoKey Terms

We are including the glossary of AutoKey terms at the beginning of the users manual because understanding our definitions of the terms, as they apply to AutoKey, will make understanding the AutoKey much easier.

- The AutoKey icon is the letter "A" that appears in the notification area or system tray when AutoKey is started. Clicking on the icon opens a pop-up menu that gives you access to AutoKey's features. The icon can be changed--either by an icon theme or in the preferences menu.
- The "tray menu" is the pop-up menu that appears when the AutoKey icon is clicked.
- "Triggers" are hotkeys and typed abbreviations.
- A "hotkey" is a key or combination of keys that, when pressed, will trigger AutoKey to do something; run a script, insert a phrase or display a menu. A hotkey can be created using any key on the keyboard (within reason), with or without one or more modifier keys. The modifier keys are Shift, Control, Alt and Super (a.k.a. Windows).
- An "abbreviation" is a short sequence of letters, numbers or symbols that when typed will trigger AutoKey to do something (run a script, insert a phrase, display a menu).
- A "script" is a small program written in Python. It can start other programs, send commands to a running window, re-size your window, reposition your cursor after execution, etc.
- A "phrase" is a text string or block of text. Phrases can include one or more scripts and their output can add content to the text (ex: current time) or modify it in other ways (ex: position, format, footnotes, etc.).
- "Folders" are displayed in the left column of the main window. They can contain sub-folders, scripts and phrases. You can add sub-folders or create new folders as needed.


## Why Would You Use AutoKey And What Does It Do For You?

AutoKey can be a huge time saver, energy saver and productivity booster and can also reduce the stress on your arms and hands.

### Some examples:

There are certain things you type over and over; your address, your company name or your custom signature. AutoKey's abbreviations can automatically expand a few characters into any of your commonly used text blocks. For programmers, AutoKey's text insertion features can let you easily insert code tags, dividers, etc. at the cursor position.

If you use database, CAD/CAM, engineering or scientific software that require complex key combinations, AutoKey can be configured to send commands that will activate those features with a single keystroke.

Instead of just inserting text, a script can be used to manipulate several different running programs, transfer text between them, start and close them as well as send keyboard and mouse input to them.

AutoKey works across all applications. Any phrase, script or abbreviation can be used in multiple applications. This means you do not have to configure all the different applications that you use--you can do it once in AutoKey and it works for all your applications.

AutoKey is very useful if you write or edit business documents, novels, documentation, articles, web blogs, programs or fill out a lot of forms.

## What Is AutoKey and How Does It Work?

It is a trigger or selection activated, automation utility program for Linux and X11. When a trigger is detected by Autokey, one of three things can happen; a script is activated, text is inserted at the cursor position or a pop-up menu is displayed allowing a script or phrase to be activated by selecting it.

AutoKey scripts can literally do almost anything that can be coded as a Python program. Python scripts are user created and can be shared between users. AutoKey includes a range of sample Python scripts, and there are countless Python scripting resources on-line for learning how to write scripts.

The core part of AutoKey works by sending and receiving keyboard events via the X server. It supports multiple ways of communicating with X and as such should --in theory-- work with any Western keyboard layout. (Problems are known to exist with Russian/Mandarin/Japanese languages)

# Common actions

## Adding Abbreviations

On the left side of the configuration window you will see a "tree" view of the folders/subfolders already in AutoKey.

Let's first add a New Top-level folder for the abbreviations you are going to add:

File > Create > New Top-level Folder. You can choose to create the new folder anywhere you wish, or you may click "Use Default" and type a name. This will create a new folder under the default folder.

Now that we have a new folder, we can start adding abbreviations.

Ensure you have the folder you want the phrase created in selected, then press Ctrl + N or use the menu or the right-click menu. The main menu option is File > Create > New Phrase. Enter a name for your phrase and click OK.

Next press the tab key to get to the big dialog window to enter the contents of your phrase. Once the phrase is entered press Ctrl + Tab to navigate via keyboard or click on the "Set" button for "Abbreviation". This will bring up a "Set Abbreviation" dialog - this is where you set the actual abbreviation for the phrase. Leave the "Trigger on" to "Default." Make sure you leave "Remove typed abbreviation" checked, unless you want to leave the abbreviation in the document for some reason.

In this example, we'll set the "Match phrase case to typed abbreviation" - this option and "Ignore case of typed abbreviation" work in concert to let your abbreviation expand with case sensitivity:

| Abbreviation | You See | 
|:-----------------|:------------| 
| tp | the patient | 
| Tp | The patient | 
| TP | THE PATIENT |

Click "OK" or type Alt to accept the abbreviation settings. One last step - click "Save" or Control + S to save the changes to the phrase.

Now, if you type the abbreviation you created in any document or window, it will be replaced with the phrase contents you created.