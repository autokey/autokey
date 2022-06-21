There's a bit of a trick to using Unicode characters in AutoKey scripts and phrases without first putting them onto the clipboard. The syntax varies slightly depending on whether you're printing one or more Unicode characters or interspersing the Unicode characters with single characters. Below are some examples.

## IN SCRIPTS:

### Important rules to keep in mind:
- You should use `keyboard.send_keys()` for these, because they're multi-byte characters.
- You cannot use `keyboard.send_key()` for these, because they're not technically single characters.
- This will only work on Unicode character-codes that use the **base-ten positional numeral system** (that contain **all digits and no letters**).
- This will display any Unicode character that has **only four digits in its Unicode character-code**.
- This will **not display the result in color** even if an actual character or emote is in color.
- If a Unicode character will be the **last or only character** you print, **an additional key-press is required to get rid of the tooltip**. In the examples, I inserted a space or a plus sign at the end of each string. Note that neither the space nor the plus sign will be printed, but are simply a way to communicate with AutoKey that you're done creating the character. If a space or plus sign is desired after the Unicode character, an additional space or plus sign must be inserted.
- You can insert as many Unicode characters as you like into a string that contains just Unicode characters. In that case, you have two choices: You can put a space or plus sign after each of the characters or just put one space or plus sign at the end of all of the characters.
- If you create a string that's a mixture of single characters and Unicode characters, each Unicode character must end with a space or plus sign.
- In any of the example scripts below, wherever you see **u** being used to reference a Unicode character, you can use **uU** instead. It does the same thing, but is alternate syntax that may be preferable.

### To print a single Unicode character:

Add a space after the Unicode character:

`keyboard.send_keys("<ctrl>+<shift>+u+0108 ")`

Or add a plus sign after the Unicode character:

`keyboard.send_keys("<ctrl>+<shift>+u+0108+")`

Result:

Ĉ

### To print several Unicode characters:

Add a space after the **last** Unicode character:

`keyboard.send_keys("<ctrl>+<shift>+u+0108<ctrl>+<shift>+u+2742<ctrl>+<shift>+u+2663<ctrl>+<shift>+u+2740 ")`

Or add a plus sign after the **last** Unicode character:

`keyboard.send_keys("<ctrl>+<shift>+u+0108<ctrl>+<shift>+u+2742<ctrl>+<shift>+u+2663<ctrl>+<shift>+u+2740+")`

Or add a space after **each** Unicode character:

`keyboard.send_keys("<ctrl>+<shift>+u+0108 <ctrl>+<shift>+u+2742 <ctrl>+<shift>+u+2663 <ctrl>+<shift>+u+2740 ")`

Or add a plus sign after **each** Unicode character:

`keyboard.send_keys("<ctrl>+<shift>+u+0108+<ctrl>+<shift>+u+2742+<ctrl>+<shift>+u+2663+<ctrl>+<shift>+u+2740+")`

Result:

Ĉ❂♣❀

### To print a mixture of single characters and Unicode characters:

Add a space after **each** Unicode character:

`keyboard.send_keys("foo<ctrl>+<shift>+u+0108 foo<ctrl>+<shift>+u+0108 foo")`

Or add a plus sign after **each** Unicode character:

`keyboard.send_keys("foo<ctrl>+<shift>+u+0108+foo<ctrl>+<shift>+u+0108+foo")`

Result:

fooĈfooĈfoo

### To print a character that won't print:
When you come across a character that won't print by using the above techniques, try putting it onto the clipboard and pasting it. Build your string in a variable or in the clipboard API call, then add a delay, and then paste it. For example:
```python
clipboard.fill_clipboard("ã")
time.sleep(0.1)
keyboard.send_keys("<ctrl>+v")
```
Result:

ã

_Note that when you operate on the clipboard, a delay is usually required after the API call to give it time to complete, because the call immediately returns successfully even though the action is being asynchronously processed in another thread. That's an artifact of the way the upstream clipboard libraries we use work and applies to both front ends._

### To wrap text around a selection that contains one or more graphical Unicode characters:
When you have some text selected in a window, if it contains Unicode characters that AutoKey won't work with, you can get around that by letting the operating system intercept your key-combinations and handle the copying and pasting for you, bypassing AutoKey entirely for that part of the task. The way it works is that the operating system copies your selected text, then AutoKey deletes your selection and inserts the first part of your wrapper, then the operating system pastes your Unicode in, and then AutoKey inserts the last part of your wrapper. In this example, the first part of the wrapper is an opening ```<p>``` tag and the last part of the wrapper is a closing ```</p>``` tag.
```
keyboard.send_keys("<ctrl>+c")
keyboard.send_keys("<p>")
keyboard.send_keys("<ctrl>+v")
keyboard.send_keys("</p>")
```
Or the same thing as a two-liner:
```
keyboard.send_keys("<ctrl>+c")
keyboard.send_keys("<p><ctrl>+v</p>")
```
Or the same thing as a one-liner:
```
keyboard.send_keys("<ctrl>+c<p><ctrl>+v</p>")
```
_Thanks go to Johnny Rosenberg and Kreezxil for coming up with this approach._

## IN PHRASES:
You can use the key-combination that creates a Unicode character inside of a phrase and it will be converted to a Unicode character. No quotes are needed around it and spaces or plus signs should be used after the key-combinations.

### Important rules to keep in mind:
- You should use the key-combination that creates a Unicode character for these (a press of the Ctrl key, Shift key, u, and the Unicode character-code done by stringing them together with plus signs).
- This will only work on Unicode character-codes that use the **base-ten positional numeral system** (that contain **all digits and no letters**).
- This will display any Unicode character that has **only four digits in its Unicode character-code**.
- This will **not display the result in color** even if an actual character or emote is in color.
- If a Unicode character will be the **last or only character** you print, **an additional key-press is required to get rid of the tooltip**. In the examples, I inserted a space or a plus sign at the end of each string. Note that neither the space nor the plus sign will be printed, but are simply a way to communicate with AutoKey that you're done creating the character. If a space or plus sign is desired after the Unicode character, an additional space or plus sign must be inserted.
- You can insert as many Unicode characters as you like into a string that contains just Unicode characters. In that case, you have two choices: You can put a space or plus sign after each key-combination or just put one space or plus sign at the end of all of the key-combination.
- If you create a string that's a mixture of single characters and Unicode characters, each key-combination must end with a space or plus sign.

### To print a single Unicode character:

Add a space after the key-combination:

`<ctrl>+<shift>+u+0108 `

Or add a plus after the key-combination:

`<ctrl>+<shift>+u+0108+`

Result:

Ĉ

Or paste the Unicode character into a phrase and change the "**Paste using**" phrase setting to "**Clipboard**".

### To print several Unicode characters:

Add a space after the **last** key-combination:

`<ctrl>+<shift>+u+0108<ctrl>+<shift>+u+0108<ctrl>+<shift>+u+0108<ctrl>+<shift>+u+0108 `

Or add a plus sign after the **last** key-combination:

`<ctrl>+<shift>+u+0108<ctrl>+<shift>+u+0108<ctrl>+<shift>+u+0108<ctrl>+<shift>+u+0108+`

Result:

Ĉ❂♣❀

Or paste the Unicode characters into a phrase and change the "**Paste using**" phrase setting to "**Clipboard**".

### To print a mixture of single characters and Unicode characters:

Add a space after **each** key-combination:

`foo<ctrl>+<shift>+u+0108 foo<ctrl>+<shift>+u+0108 foo`

Or add a plus sign after **each** key-combination:

`foo<ctrl>+<shift>+u+0108+foo<ctrl>+<shift>+u+0108+foo`

Result:

fooĈfooĈfoo
