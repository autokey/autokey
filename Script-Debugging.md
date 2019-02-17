AutoKey scripts are basically Python scripts with an AutoKey API. There are 2 different ways to debug problems in your AutoKey scripts:

**Option 1)** View AutoKey error messages

**Option 2)** Develop your scripts using normal Python, then port to AutoKey  
  
  

# Option 1) View AutoKey error messages
* You can view the dialogue box by clicking menu item `Tools`→`View script error`.
* You can access the script error dialogue via the tray icon context menu, too. Note that if you use the GTK GUI (autokey-gtk), you have to keep the main window open for it to work, until [#222](https://github.com/autokey/autokey/issues/222) is resolved.
* All scripting errors are also logged in the console output. You can exit AutoKey then start it from a terminal. eg:
`autokey-gtk --verbose`

# Option 2) Develop your scripts using normal Python, then port to AutoKey
Write your code in a normal Python script, such as "myscript.py" and execute it using any Python interpreter, such as running `python myscript.py`. You can use [`unittest.mock.MagicMock()`](https://docs.python.org/3/library/unittest.mock.html) to fake the API objects. It get's a bit more complicated if you use the values returned by AutoKey API functions and need to fake them, too. Then you’ll have to configure the Mock object to return an expected value. But if you don't care about returned values, you can just throw in something like this at the beginning of your script:

```python
from unittest.mock import MagicMock
keyboard = MagicMock()
mouse = MagicMock()
dialog = ...
```

and the script basically works outside of AutoKey, (without actual functionality, of course).
Once you've got it working OK in normal Python, copy it into AutoKey. (Remove the Mock creation code, of course.) Note that each AutoKey script is stored as a Python file in your home folder, such as `~/.config/autokey/data/My\ Phrases/` in Linux.