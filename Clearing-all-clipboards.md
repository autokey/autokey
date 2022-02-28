Autokey user scripts that use the X clipboard to select, copy, or paste, and want to clear the clipboard prior to new clipboard activity, can use the following code based on 'xsel' at the start of the script:

```
import os
os.system("sleep .1; xsel -cb")

```

Optionally, one can completely clear the X CLIPBOARD, PRIMARY, and SECONDARY memory areas at the termination of a script with the following code.

```
os.system("sleep .1; xsel -cp && sleep .1; xsel -cb && sleep .1; xsel -cs")

```
