## Get a Gmail URL from the 'Open In New Window' button

If you use the 'preview pane' view in Gmail, you will note that you cannot then see the URLs of individual messages in the address bar. Yet each message does indeed have an unique URL. To get the URL of a message without having to switch to the standard view:

* click on the 'Open In New Window' button at the top right of the message preview pane ([image](https://plus.google.com/+Gmail/posts/hvVnBaQMTfj))
* in the popup, click once in the address bar to select the URL
* run the script below (I run it from the Autokey system tray menu)
* the correct URL replace the popup's URL in your clipboard

```python
import re
url = clipboard.get_selection()
gmail_baseurl="https://mail.google.com/mail/u/0/#inbox/"
match = re.search(r'(?<=th=)(\w+)(&)', url)
clipboard.fill_clipboard(gmail_baseurl + match.group(1))
```

## Convert text case to lowercase and replace spaces with hyphens
This is useful for converting the name of a GitHub Issue into a string that's suitable for a Git branch, if you follow the style of 'named-branch' Git development.

For example:

> Unexpected Window title: FocusProxy

is returned as

> unexpected-window-title:-focusproxy

```python
text = clipboard.get_selection()
clipboard.fill_clipboard(text.lower().replace(' ', '-'))
```

## Automatically collect and paste information about the current platform
Useful for making bug reports especially on web applications where the platform and browser version may be relevant.

example:

> Platform: Linux-4.13.0-37-generic-x86_64-with-LinuxMint-18.3-sylvia
> Browser: Google Chrome 65.0.3325.181 
> Browser: Mozilla Firefox 59.0.1
> Date Tested :Wed 28 Mar 14:46:48 BST 2018

```python
import platform
output = ""
output += "Platform: " + platform.platform() + "\n"
output += "Browser: " + os.popen("google-chrome --version").read()
output += "Browser: " + os.popen("firefox --version").read()
output += "Date Tested :" + system.exec_command("date")
keyboard.send_keys(output)
```

