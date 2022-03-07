Autokey user scripts that use the X clipboard to select, copy, or paste, and want to clear the clipboard prior to new clipboard activity, can use the following code based on 'xsel' at the start of the script:

```
import os
os.system("sleep .1; xsel -cb")

```

Optionally, one can completely clear the X CLIPBOARD, PRIMARY, and SECONDARY memory areas at the termination of a script with the following code.

```
os.system("sleep .1; xsel -cp && sleep .1; xsel -cb && sleep .1; xsel -cs")

```

To test the code, paste the string in a terminal (without the quotes) and it must return without error.

The os.system() call from Python (in this case Autokey) must be enclosed with a single set of double quotes.

Multiple double quotes in the string fail. Single quotes also fail and the differences between the quotes are well documented in Linux.

The xsel command "os.system(xsel -cbps)", to clear all memory areas in a single switch, did not work for me.

Prior to, and between each memory area, a 0.1 second pause was required for each command execution to be successful
- based on the amount of memory used in the context of my copy and paste activity.

Tested the order of the xsel memory areas to be cleared under various copy and paste activity,

Starting a script that uses the clipboard, with this .1 second delay, clearing was always successful.

I tested this between several simultaneous open Linux apps and between Linux apps and Windows apps running in Wine. Autokey must be disabled to successfully use a wine\Windows app.

```

sleep .1; xsel -cb && sleep .1; xsel -cp && sleep .1; xsel -cs

```

or use this script

```
#!/usr/bin/bash

## 2022-02-18 17:16 - clear_clipboard.sh

## -c = CLEAR, b = CLIPBOARD, p = PRIMARY, s = SECONDARY, --display:0 = DISPLAY in milliseconds

## when pasted individually

# sleep .1
# xsel -cb
# sleep .1
# xsel -cp
# sleep .1
# xsel -cs

sleep .1; xsel -cb && sleep .1; xsel -cp && sleep .1; xsel -cs

```
