I'm having the same issue as this [guy](https://groups.google.com/g/autokey-users/c/2ZxvpRy5Iag/m/ctThDLbKBAAJ?pli=1).

I need the ability to script an actual paste from the clipboard instead of sending each keystroke individually from the clipboard.

You see, in remote RDP sessions, I lose keystrokes when sending keys the normal way, but if I could tell my script to paste what's in the clipboard, instead of sending each keystroke, I wouldn't lose any characters.

Since I cannot find anything in the API that does this, I'm having to fill_clipboard in script and manually press ctrl-v after doing so. I'm just trying to automate away that last step of having to press ctrl-v.

I just tried sending ctrl-v like this:
keyboard.send_key("<control>v")

It crashed Autokey!