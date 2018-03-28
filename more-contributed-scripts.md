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
