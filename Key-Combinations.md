# Key Combinations
Keys and key combinations can be pressed for you automatically by AutoKey in a variety of ways, with the methods below being built in for your convenience.

***

## Key combinations in phrases:

#### About:

You can insert any number of key combinations into phrases.

#### Examples:

```
example<backspace>This line will send some text followed by a backspace followed by this text.

<delete>This line will send a delete followed by this text.

This line will send this text followed by the number seven from the numpad.<numlock>+<code79>

This line will send this text followed by a vulgar one-tenth fraction. <ctrl>+<shift>+u+2152

This line will send this text and press the keys below, but the key-combination will only work in the focused window and not globally.

<shift><ctrl>+o
```

***

## Key combinations in scripts:

### The keyboard.send_key() method:

#### About:

The `keyboard.send_key()` method accepts only one key.

#### Examples:

##### Press and release one key:
```
keyboard.send_key("<tab>")
```

***

### The keyboard.fake_keypress() method:
This method can be useful for sending key-presses if an application doesn't respond to the `keyboard.send_key()` method.

#### Press the up arrow three times:
```
keyboard.fake_keypress("<up>", repeat=3)
```

***

### The keyboard.send_keys() method:

#### About:
The `keyboard.send_keys()` method accepts any number of keys. A plus sign between keys causes the keys on either side of it to be pressed at the same time. Leaving off the plus sign between keys causes them to be pressed and released one after another. With a combination of both approaches in the same statement, you can achieve a variety of key-press combinations.

#### Examples:

##### Press and release one key:
```
keyboard.send_keys("<tab>")
```
##### Press and release one key after another:
```
keyboard.send_keys("ab")
```
##### Press and release two keys at once:
```
keyboard.send_keys("<shift>+a")
```
##### Press and release two keys at once and then press and release another key:
```
keyboard.send_keys("<shift>+at")
```
##### Press and release two keys at once and then press and release more keys one after another:
```
keyboard.send_keys("<ctrl>+<alt>pb")
```
##### Press and release two keys at once and then press and release more keys one after another:
```
keyboard.send_keys("<shift>+apple")
```

***

### The keyboard.press_key() and keyboard.release_key() methods:

##### Press and release one key:
```
keyboard.press_key("<tab>")
keyboard.release_key("<tab>")
```

##### Press and release one key after another:
```
keyboard.press_key("a")
keyboard.release_key("a")
keyboard.press_key("b")
keyboard.release_key("b")
```

##### Press and release two keys at once:
```
keyboard.press_key("<shift>")
keyboard.press_key("a")
keyboard.release_key("a")
keyboard.release_key("<shift>")
```

##### Press and release two keys at once and then press and release another key:
```
keyboard.press_key("<shift>")
keyboard.press_key("a")
keyboard.release_key("a")
keyboard.release_key("<shift>")
keyboard.press_key("t")
keyboard.release_key("t")
```

##### Press one key, then press and release more keys one after another, then release the first key:
_(NOTE: This is not possible with the other methods.)_
```
keyboard.press_key("<shift>")
keyboard.press_key("a")
keyboard.release_key("a")
keyboard.press_key("b")
keyboard.release_key("b")
keyboard.press_key("c")
keyboard.release_key("c")
keyboard.release_key("<shift>")
```

##### Press and release two keys at once and then press and release more keys one after another:
```
keyboard.press_key("<shift>")
keyboard.press_key("a")
keyboard.release_key("a")
keyboard.release_key("<shift>")
keyboard.press_key("p")
keyboard.release_key("p")
keyboard.press_key("p")
keyboard.release_key("p")
keyboard.press_key("l")
keyboard.release_key("l")
keyboard.press_key("e")
keyboard.release_key("e")
```

***

### Notes:

#### About the keyboard.send_key() and keyboard.send_keys() methods and case:
When using the ```keyboard.send_key()``` method, AutoKey doesn't press the **Shift** key on keys that have more than one value.
When using the ```keyboard.send_keys()``` method, AutoKey presses the **Shift** key on keys that have more than one value.
The alphabet keys, for example, each only have one value on them, so those will be lower-case (even if the Caps Lock key is enabled).
To send single-value keys in upper-case, you'd have to explicitly tell AutoKey to send a press of the **Shift** key before a press of the single-value key.

#### Get the key code of any key:
In Linux, you can run the ```xev``` command in a terminal window and then press any key(s) to get their their keycode(s). Mac and Windows may offer something similar.
