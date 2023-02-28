### Creating New Modifier Keys ###
[Tutorial](https://youtu.be/pDrPr4PcytY) by Dell Anderson - New (10/2017)

This short tutorial shows you how to assign a key to Hyper-R so you can use it in addition to the more common modifier keys like Super, Shift, Alt, and Ctrl.

### Writing Scripts Which Do More Than One Thing ###

We get a number of questions about getting AutoKey to do things like detecting keypresses, holding keys down, or interacting with the computer and user based on more than one event.

AutoKey is designed to continue detecting triggers even when a script is currently executing. So scripts that run for some time are possible and will not stop subsequent scripts from being triggered. However, actually assuring that things happen in the expected order/timing is left as an exercise for the reader. ;)

It is quite possible to write errant script code which can get stuck in a loop when unexpected events occur. This can cause AutoKey or sometimes the whole desktop to become unresponsive, so care should be taken when coding anything complex or concurrent.

Another feature of AutoKey is that two or more scripts/phrases can have the same trigger phrase or hotkey as long as they are defined with mutually exclusive window/class filters.

So, for example, a utility for processing multiple variations of print dialogs from different applications could be coded as several separate scripts - one for each variation - rather than as one complex script with conditional code for each variation - with all of them triggered by pressing Ctrl+P.

NOTE: Assuring that these filters are mutually exclusive is the responsibility of the user. AutoKey only detects and rejects identical filters for the same trigger. (It turns out that detecting that two regexes are mutually exclusive is a very difficult problem. It is not clear if it is even generally solvable.)

If two different actions using the same trigger have different non-mutually exclusive filters, the behavior is undefined, but the first match found (in whatever order the search is done) is probably the one which will succeed.