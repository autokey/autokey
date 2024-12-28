### Special Considerations for Using Special Keys In Hotkey Combinations ###

When you are assigning a hotkey combination to a script, it is important to recognize that a special key used as part of the hotkey combination might have unexpected effects on the behavior of the script.  This might be best explained through an example:

Let us suppose that we want to make it so that the ```<left_meta>+x``` hotkey combination will perform a ```mouse.scroll_down(2)``` command, making the window that has focus scroll down slightly, as if we had moved our mouse wheel down two clicks.  We would create a script with one line of code like the one below and assign it to the ```<left_meta>+x``` hotkey.
```
mouse.scroll_down(2)
```
***Note:*** The ```<left_meta>``` key is sometimes also called the Super key.  It's often located to the left of the spacebar and has the Microsoft Windows logo on it.

Now, when we press the ```<left_meta>+x``` hotkey combination, the window does not scroll down as we expected, instead the display jumps to the next workspace in our desktop environment, assuming we have it configured for multiple workspaces, or does nothing if we only have one workspace defined.  (For this example we're assuming that we're using the GNOME desktop manager.  Other environments might behave differently given their particular hotkey assignments, but the principle remains the same.)

The reason the script didn't do what we expected it to do is because the ```<left_meta>``` key was still being held down when the script sent the ```mouse.scroll_down(2)``` action and so the desktop did what it's configured to do when the user holds down the meta key and moves their mouse wheel, it toggled the active workspace.  As humans, we cannot release the meta key fast enough to avoid having it modify the behavior of the ```mouse.scroll_down(2)``` command sent by the script.

We can overcome this problem by telling the script to release the ```<left_meta>``` key for us, before it sends the mouse action, changing our script to this:
```
keyboard.release_key("<left_meta>")
mouse.scroll_down(2)
```
The moral of this story is, when things go wrong, consider how a special key used as part of a hotkey might interact with the actions coded into the script.
### Creating New Modifier Keys ###
[Tutorial](https://youtu.be/pDrPr4PcytY) by Dell Anderson - New (10/2017)

This short tutorial shows you how to assign a key to Hyper-R so you can use it in addition to the more common modifier keys like Super, Shift, Alt, and Ctrl.

### Writing Scripts Which Do More Than One Thing ###

We get a number of questions about getting AutoKey to do things like detecting keypresses, holding keys down, or interacting with the computer and user based on more than one event.

AutoKey is designed to continue detecting triggers even when a script is currently executing. So scripts that run for some time are possible and will not stop subsequent scripts from being triggered. However, actually assuring that things happen in the expected order/timing is left as an exercise for the reader. ;)

It is quite possible to write errant script code which can get stuck in a loop when unexpected events occur. This can cause AutoKey or sometimes the whole desktop to become unresponsive, so care should be taken when coding anything complex or concurrent.

Another feature of AutoKey is that two or more scripts/phrases can have the same trigger phrase or hotkey as long as they are defined with mutually exclusive window/class filters.

So, for example, a utility for processing multiple variations of print dialogs from different applications could be coded as several separate scripts - one for each variation - rather than as one complex script with conditional code for each variation - with all of them triggered by pressing Ctrl+P.

NOTE: Assuring that these filters are mutually exclusive is the responsibility of the user. AutoKey only detects and rejects identical filters for the same trigger. (It turns out that detecting that two regexes are mutually exclusive is not generally solvable. See #365 for an enhancement request with a possible wokaround for this.)

If two different actions using the same trigger have different non-mutually exclusive filters, the behavior is undefined, but the first match found (in whatever order the search is done) is probably the one which will succeed.