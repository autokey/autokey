## Table of Contents

  * [Modules - about](#modules---about)
  * [Modules - internal](#modules---internal)
    * [Choose a folder for use by AutoKey for modules](#choose-a-folder-for-use-by-autokey-for-modules)
    * [Example 1 - internal module](#example-1---internal-module)
    * [Example 2 - internal module using the API injector](#example-2---internal-module-using-the-api-injector)
    * [Change the internal module](#change-the-internal-module)
    * [Remove or change the internal module folder](#remove-or-change-the-internal-module-folder)
  * [Modules - external](#modules---external)
    * [Example 1 - external module](#example-1---external-module)
    * [Example 2 - external module using the API injector](#example-2---external-module-using-the-api-injector)
  * [Modules - see also](#see-also)

## Modules - about
AutoKey can use internal and external modules. There are two types of modules -- internal and external:
* Internal modules are modules that you store in AutoKey's user-defined modules folder.
* External modules are modules that you store anywhere on your system.

_**Note:** Examples are included below showing how modules are used. Some are for a fictional user named Dave. When following the examples, you would replace Dave's username and/or path with yours._

## Modules - internal
You can store your Python files in AutoKey's **User Module Folder**. Any modules you put in there can be directly imported into your AutoKey scripts to add functionality without having to duplicate them in each script. AutoKey's API calls aren't available to modules by default, but [the API injector](https://github.com/autokey/autokey/issues/248) is a work-around for that.

### Choose a folder for use by AutoKey for modules
There isn't a **User Module Folder** by default, but you can choose one in one of these ways:

* In the **AutoKey GTK** front-end:
	1. Open the **Edit** menu.
	2. Choose **Preferences** from the menu.
	3. Click the **Script Engine** tab.
	4. Click the dropdown selector.
	5. Choose a folder.
	6. Click the **Open** button.
	7. Click the **OK** button.
* In the **AutoKey Qt** front-end:
	1. Open the **Settings** menu.
	2. Choose **Configure AutoKey** from the menu.
	3. Click **Script Engine** in the left pane.
	4. Click the **Browse** button.
	5. Browse to the folder you'd like to use.
	6. Click the **OK** button.
	7. Click the **Save** button.

If the folder you chose isn't recognized by AutoKey:

1. Close AutoKey.
1. Open the ```~/.config/autokey/autokey.json``` file in a text editor.
1. Find the line that looks like this: ```"userCodeDir": "",```
1. Put your directory path in manually. For example: ```"userCodeDir": "/home/dave/modules",```
1. Save the file.

Once your Python files are in the **User Module Folder** you chose, you can use an import statement in any AutoKey script to use their contents. For example, if you created the ```my_module.py``` file in your AutoKey **User Module Folder**, then you can use the ```import my_module``` statement in any script to make its contents available in that script. Note that you'll need to use the module's name to invoke any of its objects. For example, ```my_module.my_variable``` would use the ```my_variable``` variable from inside of the ```my_module``` module.

#### Example 1 - internal module
1. Create the ```my_module.py``` file inside of the folder you've chosen for your AutoKey modules and put these contents into it:

```python
#!/usr/bin/env python3

# Create a variable with a string as its value:
variable1="one"

# Create a variable with a string as its value:
variable2="two"

# Create a function that returns a string:
def function1():
	return "three"
```

2. Create an AutoKey script with these contents to import your module and use its objects:

```python
# Import the necessary module:
import my_module

# Display the value of a variable from the imported module in a dialog:
dialog.info_dialog(message=my_module.variable1)

# Display the value of a variable from the imported module in a dialog:
dialog.info_dialog(message=my_module.variable2)

# Display the value of the function from the imported module in a dialog:
dialog.info_dialog(message=my_module.function1())
```

This displays three dialogs, one after another, when the AutoKey script is run.

#### Example 2 - internal module using the API injector
1. Create the ```my_module.py``` file inside of the folder you've chosen for your AutoKey modules and put these contents into it to inject and use the AutoKey API:

```python
#!/usr/bin/env python3

# Create a function that injects the AutoKey API into this Python module/script:
def load_api(api_keyboard, api_mouse, api_store, api_system, api_window, api_clipboard, api_highlevel, api_dialog, api_engine):
	# Create the API global variables:
	global keyboard, mouse, store, system, window, clipboard, highlevel, dialog, engine
	# Define each API global variable with its API class instance:
	keyboard = api_keyboard
	mouse = api_mouse
	store = api_store
	system = api_system
	window = api_window
	clipboard = api_clipboard
	highlevel = api_highlevel
	dialog = api_dialog
	engine = api_engine

# Create a variable with a string as its value:
greeting="This is the value of a variable in this module."

# Create a function that returns a string:
def testing1():
	return "This is the return value of a function in this module."

# Create a function that uses the AutoKey API to display a dialog:
def testing2():
	dialog.info_dialog(message="This is an API dialog from within a function in this module.")
```

2. Create an AutoKey script with these contents to import and use that module to create a few example objects:

```python
# Import the necessary module:
import my_module

# Inject the AutoKey API into the module:
my_module.load_api(keyboard, mouse, store, system, window, clipboard, highlevel, dialog, engine)

# Display the value of a variable from the imported module in a dialog:
dialog.info_dialog(message=my_module.greeting)

# Display the value of a function from the imported module in a dialog:
dialog.info_dialog(message=my_module.testing1())

# Run the module's testing2 function to display a dialog:
my_module.testing2()
```

This displays three dialogs, one after another, when the AutoKey script is run. Two were initiated by the AutoKey script and one was initiated by the Python module using the injector.

### Change the internal module
You can change the code inside the internal module while AutoKey is running, but there's a [known issue](https://github.com/autokey/autokey/issues/747) that prevents AutoKey from noticing changes to the internal module while AutoKey is running, so you'll need to close and restart AutoKey afterwards:
1. Close AutoKey.
2. Open a terminal window.
3. Type this command to check if the AutoKey process has closed:
```
pgrep -c autokey
```
4. If the output is a zero, the AutoKey process has closed and you can go to the next step. If the output is a 1, the AutoKey process is still running, so you'll need to type this command to end the process and then return to step 3:
```
pkill autokey
```
5. Launch AutoKey.

### Remove or change the internal module folder
You can change the **User Module Folder** to another one by following the steps above for setting up a **User Module Folder** and choosing a different folder, but if you'd like to just remove the folder you've chosen without choosing another one, that will have to be done manually.

1. Close AutoKey.
2. Open ```~/.config/autokey/autokey.json``` in a text editor.
3. Find a line that starts with ```"userCodeDir"``` that looks like this example one, but with the path to your **User Module Folder** in it:
	```python
	"userCodeDir": "/home/dave/mymodules",
	```
4. Replace that line with this one:
	```python
	"userCodeDir": "",
	```
5. Save the file.

## Modules - external
You can create and store your Python files anywhere on your system and use them as modules that you can import into your AutoKey scripts to add functionality without having to duplicate them in each script. This is done by using the **importfile** class from the **pydoc** library. AutoKey's API calls aren't available to modules by default, but [the API injector](https://github.com/autokey/autokey/issues/248) is a work-around for that.

### Example 1 - external module:
Create the ```example.py``` file on the Desktop with these contents:

```python
#!/usr/bin/env python3

variable1="one"
variable2="two"

def function1():
	return "three"
```

Create an AutoKey script that imports and uses the module (replace Dave's path with yours):

```python
# Import the necessary class from the necessary library:
from pydoc import importfile

# Import an external module from anywhere:
my_module = importfile('/home/dave/Desktop/example.py')

# Display the value of a variable from the imported module in a dialog:
dialog.info_dialog(message=my_module.variable1)

# Display the value of a variable from the imported module in a dialog:
dialog.info_dialog(message=my_module.variable2)

# Display the value of the function from the imported module in a dialog:
dialog.info_dialog(message=my_module.function1())
```

This displays three dialogs, one after another, when the AutoKey script is run.

### Example 2 - external module using the API injector
1. Create the ```example.py``` file on the Desktop with these contents to inject and use the AutoKey API:

```python
#!/usr/bin/env python3

# Create a function that injects the AutoKey API into this Python module/script:
def load_api(api_keyboard, api_mouse, api_store, api_system, api_window, api_clipboard, api_highlevel, api_dialog, api_engine):
	# Create the API global variables:
	global keyboard, mouse, store, system, window, clipboard, highlevel, dialog, engine
	# Define each API global variable with its API class instance:
	keyboard = api_keyboard
	mouse = api_mouse
	store = api_store
	system = api_system
	window = api_window
	clipboard = api_clipboard
	highlevel = api_highlevel
	dialog = api_dialog
	engine = api_engine

# Create a variable with a string as its value:
greeting="This is the value of a variable in an external module."

# Create a function that returns a string:
def testing1():
	return "This is the return value of a function in an external module."

# Create a function that uses the AutoKey API to display a dialog:
def testing2():
	dialog.info_dialog(message="This is an API dialog from within a function in an external module.")
```

2. Create an AutoKey script with these contents to import and use that module to create a few example objects (replace Dave's path with yours):

```python
# Import the necessary class from the necessary library:
from pydoc import importfile

# Import an external module from anywhere:
mymodule = importfile('/home/dave/Desktop/example.py')

# Inject the AutoKey API into the module:
mymodule.load_api(keyboard, mouse, store, system, window, clipboard, highlevel, dialog, engine)

# Display the value of a variable from the imported module in a dialog:
dialog.info_dialog(message=mymodule.greeting)

# Display the value of a function from the imported module in a dialog:
dialog.info_dialog(message=mymodule.testing1())

# Run the module's testing2 function to display a dialog:
mymodule.testing2()
```

This displays three dialogs, one after another, when the AutoKey script is run. Two were initiated by the AutoKey script and one was initiated by the Python module using the injector.

## See also
* See also [this AutoKey discussion](https://github.com/autokey/autokey/issues/248) about injecting API functions into user modules.
* See also [this AutoKey discussion](https://github.com/autokey/autokey/discussions/743) about running non-local code in an AutoKey script.
* AutoKey scripts can run other AutoKey scripts with the ```engine.run_script(...)``` API call. See the [Run an AutoKey script from another AutoKey script](https://github.com/autokey/autokey/wiki/Advanced-Scripts#run-an-autokey-script-from-another-autokey-script) section of the [Advanced Scripts](https://github.com/autokey/autokey/wiki/Advanced-Scripts) page for a description and an example.
