## Contents

* [Global values](#global-values)
   * [Example script](#example-script)
* [Local values](#local-values)
   * [Example script](#example-script-1)

AutoKey offers two different kinds of persistent values for use in AutoKey scripts: global and local values. These are key/value pairs that are "remembered" for you by AutoKey from session to session.

## <a id="global-values">Global values
- Global values are user-specified JSON key/value pair objects.
- They accept any hashable object as a key and any serializable Python object as a value.
- In Python, anything is an object (classes, functions, data types, etc.), but classes and functions are not serializable.
- Global values can be created, accessed, and managed from within any AutoKey scripts.
- They're available for use by all AutoKey scripts.
- They can be changed in the same way that they're created - with a statement that sets a key/value pair.
- Global values are kept in the AutoKey store.
- The store is the **scriptGlobals** object inside of the `~/.config/autokey/autokey.json` file.
- Global values are created in, changed in, or removed from that object inside that file at the end of the AutoKey session in which the change occurred.
- Deleting the set statement (that created a global value) from a script will not remove the global value from the store.
- Deleting the script that created a global value will not delete the global value from the store.
- Global values exist until a script tells AutoKey to remove them.
- Global values may be lost if AutoKey dies by being killed from an external command or a power failure, etc.

### <a id="example-script">Example script
This example script demonstrates some of the more common things you can do with global values: creating, changing, testing for, getting, displaying, printing, and removing a global value.
```python
# Create a global value:
store.set_global_value("foo","bar")

# Change the global value:
store.set_global_value("foo","baz")

# Test for the presence of the global value:
if store.get_global_value("foo"):
    # Display a dialog letting us know it exists:
    dialog.info_dialog(title="Exists?", message="Global value exists", width="200")
    # Print a message in the active window letting us know it exists:
    keyboard.send_keys("Global value exists.")
# Otherwise:
else:
    # Display a dialog letting us know it doesn't exist:
    dialog.info_dialog(title="Exists?", message="Global value doesn't exist", width="200")
    # Print a message in the active window letting us know it doesn't exist:
    keyboard.send_keys("Global value doesn't exist.")

# Get the global value and store it in a local variable:
x = store.get_global_value("foo")

# Display the value of the local variable
dialog.info_dialog(title="Value", message=x, width="200")

# Print the value of the local variable in the active window:
keyboard.send_keys(x)

# Remove the global value:
store.remove_global_value("foo")

# Remove the local variable:
del x
```

## <a id="local-values">Local values
- Local values are user-specified JSON key/value pair objects.
- They accept any hashable object as a key and any serializable Python object as a value.
- In Python, anything is an object (classes, functions, data types, etc.), but classes and functions are not serializable.
- They can be created from within any AutoKey scripts.
- Each one can be accessed or managed from within the AutoKey script that created it.
- Local values can be changed in the same way that they're created - with a statement that sets a key/value pair.
- Local values are kept in the AutoKey store.
- The store is the **store** object inside of the `~/.config/autokey/data/Scripts` directory in the `.SCRIPTNAME.json` file with **SCRIPTNAME** being the name of the script that created the local value.
- Local values are created in, changed in, or removed from that object inside that file.
- They're written to that file the next time their AutoKey script is saved.
- Changes to local values, including removal of local values, are also written to that file the next time their AutoKey script is saved.
- Deleting a set statement from a script will not remove a local value from the store.
- Local values exist until their script tells AutoKey to remove them or until their script is deleted.
- Local values may be lost if AutoKey dies by being killed from an external command or a power failure, etc.

### <a id="example-script-1">Example script
This example script demonstrates some of the more common things you can do with local values: creating, changing, testing for, getting, displaying, printing, and removing a local value, and also displaying the store's local values.

```python
# Create a local value:
store.set_value("foo","bar")

# Change a local value:
store.set_value("foo","baz")

# Check for the presence of the local value:
if store.has_key("foo"):
    # Display a dialog letting us know the local value exists:
    dialog.info_dialog(title="Exists?", message="Local value exists", width="200")
    # Print a message in the active window letting us know the local value exists:
    keyboard.send_keys("Local value exists.")
# Otherwise:
else:
    # Display a dialog letting us know the local value doesn't exist:
    dialog.info_dialog(title="Exists?", message="Local value doesn't exist", width="200")
    # Print a message in the active window letting us know the local value doesn't exist:
    keyboard.send_keys("Local value doesn't exist.")

# Get the local value and store it in a local variable:
x = store.get_value("foo")

# Display the value of the local variable
dialog.info_dialog(title="Value", message=x, width="200")

# Print the value of the local variable in the active window:
keyboard.send_keys(x)

# Remove the local value:
store.remove_value("foo")

# Remove the local variable:
del x

# Display the AutoKey store's local values in a dialog (displays empty brackets when there are none):
import json
dialog.info_dialog(message=json.dumps(store))
```
