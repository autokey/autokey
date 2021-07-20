The way AutoKey API works with emitting keypresses is less than obvious. The following may help you to get the behavior you desire.

Never use `keyboard.send_key()` unless nothing else works (or you need its repeat parameter). Always use `keyboard.send_keys()`. `keyboard.send_key()` can only deal with single keypresses of things that appear on your physical keyboard. It doesn't deal with things like modifier keys such as Shift.

`keyboard.send_keys()` is somewhat better. It can do things like `keyboard.send_keys("<shift>+[")` to get a left curly brace or send longer strings `keyboard.send_keys("my string")`. It does have some limitations. It can't deal with multibyte characters (anything other than EN-US) and it is very limited in dealing with anything you can't generate with normal physical keypresses without getting convoluted.

You do need to use `keyboard.send_keys()` when the target application needs to respond to individual keystrokes such as `<down>` or `<right>`. 

Whenever possible, put whatever you want to emit into a string, load it into the clipboard `clipboard.fill_clipboard("my string, optionally with multibyte characters in it")`, and then paste it using `keyboard.send_keys("<ctrl>+V")`. This will almost always work and avoids a bunch of other problems.

Note that when you operate on the clipboard, a delay is usually required after the API call to give it time to complete, because the call immediately returns successfully even though the action is being asynchronously processed in another thread. That's an artifact of the way the upstream clipboard libraries we use work and applies to both front ends. `time.sleep(0.1)` will usually be sufficient

With phrases, always start with the Paste using clipboard (Ctrl+V) option unless your phrase needs to include macros such as `<cursor>` or active keys that the application has to respond to directly like arrow keys.

I've never quite figured out what `keyboard.fake_keypress()` is for, but it's worth trying when nothing else works.

For more information on creating special keypress sequences see this [article](https://github.com/autokey/autokey/wiki/Key-Combinations) as well as [this one](https://github.com/autokey/autokey/wiki/Adding-Unicode-Characters-or-Emojis-to-Your-Scripts-or-Phrases) for using Unicode characters.

Note: Need to merge some text from #547 here.