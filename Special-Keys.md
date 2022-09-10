AutoKey offers several API-supported special keys for use in your phrases or scripts and you can also customize some of your own.

***
## Table of Contents
* [API-supported special keys](https://github.com/autokey/autokey/wiki/Special-Keys#api-supported-special-keys)
* [Customized special keys](https://github.com/autokey/autokey/wiki/Special-Keys#customized-special-keys)
* [Using special keys](https://github.com/autokey/autokey/wiki/Special-Keys#customized-special-keys)
* [See also](https://github.com/autokey/autokey/wiki/Special-Keys/#see-also)
***

# API-supported special keys

The below table lists all the names used for special keys.

| Keys | String |
|:---------|:-----------|
| ALT | \<alt> |
| ALT_GR | \<alt_gr> |
| BACKSPACE | \<backspace> |
| CAPSLOCK | \<capslock> |
| CONTROL | \<ctrl> |
| DELETE | \<delete> |
| DOWN | \<down> |
| END | \<end> |
| ENTER/RETURN | \<enter> |
| ESCAPE | \<escape> |
| F1-F35 * | \<f1>-\<f35> |
| HOME | \<home> |
| INSERT | \<insert> |
| LEFT | \<left> |
| MENU | \<menu> |
| NP_ADD | \<np_add> |
| NP_BEGIN | \<np_5> |
| NP_DELETE | \<np_delete> |
| NP_DIVIDE | \<np_divide> |
| NP_DOWN | \<np_down> |
| NP_END | \<np_end> |
| NP_HOME | \<np_home> |
| NP_INSERT | \<np_insert> |
| NP_LEFT | \<np_left> |
| NP_MULTIPLY | \<np_multiply> |
| NP_PAGE_DOWN | \<np_page_down> |
| NP_PAGE_UP | \<np_page_up> |
| NP_RIGHT | \<np_right> |
| NP_SUBTRACT | \<np_subtract> |
| NP_UP | \<np_up> |
| NUMLOCK | \<numlock> |
| PAGE_DOWN | \<page_down> |
| PAGE_UP | \<page_up> |
| PAUSE | \<pause> |
| PRINT_SCREEN | \<print_screen> |
| RETURN/ENTER | \<enter> |
| RIGHT | \<right> |
| SCROLL_LOCK | \<scroll_lock> |
| SHIFT | \<shift> |
| SPACE | (space character) |
| SUPER | \<super> |
| TAB | \<tab> |
| UP | \<up> |

_*: \<F13>-\<F35> were present on some keyboards in the 80s. Although those are no longer present on modern keyboards, X11 still supports these keys. You can assign those keys as hotkeys in applications and use them from within AutoKey to trigger the assigned actions. Application support for the upper Function keys varies, as some GUI toolkits may not support them._

# Customized special keys
Keys that aren't listed in the AutoKey API can still be pressed and released as long as you know their X keycodes. In Linux, you can run the **xev** command in a terminal window and then press a key to see its data. There will be a lot of output that will be duplicated each time you press and release a key, because the xev command reacts to a key press and a key release as separate events. What you'll be looking for is the number after **keycode** in the output.

To display all output from any input device:
```bash
xev
```

To display all output from only the keyboard:
```bash
xev -event keyboard
```

To display the word "keycode" followed by the keycode:
```bash
xev -event keyboard | grep -Eo ".{,0}keycode.{,4}"
```

To display only the keycode:
```bash
xev -event keyboard | grep -Po '(?<=keycode\s)[^\s]*'
```
A key's keycode can be used in a custom code string. For example, the left Shift key's keycode is 50, so it uses the `<code50>` string, whereas the right Shift key's keycode is 62, so it uses the `<code62>` string.

# Using special keys
There are several ways to add special keys to your phrases or scripts:

* To use special keys in a phrase, insert their strings anywhere.

* To use a special keys in a script, use their strings with any of AutoKey's several [Keyboard API calls](https://github.com/autokey/autokey/wiki/API-Examples#keyboard). Some examples:
  * The **press_key** and **release_key** API calls can be used to press and release one key (the right Shift key in this example):
    ```python
    keyboard.press_key("<code62>")
    keyboard.release_key("<code62>")
    ```
  * The **send_key** call can be used to press and release one key (the right Shift key in this example):
    ```python
    keyboard.send_key("<code62>")
      ```
  * The **send_keys** call can be used to press and release more than one key:
    * To press and release two keys at the same time (the Ctrl and Escape keys in this example), insert a plus sign between their strings:
      ```python
      keyboard.send_keys("<ctrl>+<esc>")
      ```
    * To press and release two (or more) keys, one after another (the Ctrl and Escape keys in this example), include their strings without anything between them:
      ```python
      keyboard.send_keys("<ctrl><esc>")
      ```
  
# See also
* For more information on key combinations, see the [Key Combinations](https://github.com/autokey/autokey/wiki/Key-Combinations) page.
* For more information on the keyboard API calls, see the [Keyboard](https://github.com/autokey/autokey/wiki/API-Examples#keyboard) section of the API wiki page.
* For more information on the NP_BEGIN key, see this [StackOverflow](https://stackoverflow.com/questions/25259852/what-is-the-begin-key) page.
