# Key Combinations
Keys and key combinations can be pressed for you automatically by AutoKey in a variety of ways, with the methods below being built in for your convenience.


***


## The keyboard.send_key() method:

### About:

The `keyboard.send_key()` method accepts only one key.

### Examples:

#### Press and release one key:
```
keyboard.send_key("<tab>")
```


***


## The keyboard.send_keys() method:

### About:
The `keyboard.send_keys()` method accepts any number of keys. A plus sign between keys causes the keys on either side of it to be pressed at the same time. Leaving off the plus sign between keys causes them to be pressed and released one after another. With a combination of both approaches in the same statement, you can achieve a variety of key-press combinations.

### Examples:

#### Press and release one key:
```
keyboard.send_keys("<tab>")
```
#### Press and release one key after another:
```
keyboard.send_keys("ab")
```
#### Press and release two keys at once:
```
keyboard.send_keys("<shift>+a")
```
#### Press and release two keys at once and then press and release another key:
```
keyboard.send_keys("<shift>+at")
```
#### Press and release two keys at once and then press and release more keys one after another:
```
keyboard.send_keys("<ctrl>+<alt>pb")
```
#### Press and release two keys at once and then press and release more keys one after another:
```
keyboard.send_keys("<shift>+apple")
```


***


## The keyboard.press_key() and keyboard.release_key() methods:

#### Press and release one key:
```
keyboard.press_key("<tab>")
keyboard.release_key("<tab>")
```
#### Press and release one key after another:
```
keyboard.press_key("a")
keyboard.release_key("a")
keyboard.press_key("b")
keyboard.release_key("b")
```
#### Press and release two keys at once:
```
keyboard.press_key("<shift>")
keyboard.press_key("a")
keyboard.release_key("a")
keyboard.release_key("<shift>")
```
#### Press and release two keys at once and then press and release another key:
```
keyboard.press_key("<shift>")
keyboard.press_key("a")
keyboard.release_key("a")
keyboard.release_key("<shift>")
keyboard.press_key("t")
keyboard.release_key("t")
```
#### Press one key, then press and release more keys one after another, then release the first key:
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
#### Press and release two keys at once and then press and release more keys one after another:
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
