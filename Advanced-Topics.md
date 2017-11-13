### Creating New Modifier Keys ###
[Tutorial](https://youtu.be/pDrPr4PcytY) by Dell Anderson - New (10/2017)

This short tutorial shows you how to assign a key to Hyper-R so you can use it in addition to the more common modifier keys like Super, Shift, Alt, and Ctrl.

### Writing Macros Which Do More Than One Thing ###

We get a number of questions about getting AutoKey to do things like detecting keypresses, holding keys down, or interacting with the computer and user based on more than one event.

TL;DR: If you're already a somewhat skilled programmer and have a little understanding of how desktops work and some time to invest, most things like this are probably doable. So far, no one has come back with a success (or failure) story.

*The AutoKey paradigm:* a trigger event (trigger phrase/hotkey/menu item selected) occurs, an action (macro/phrase) is executed and terminates, then AutoKey goes back to waiting for the next event.

This has two consequences:

1) AutoKey is really good at doing one thing/action at a time. It is not "good" for more complex sequences.

2) In particular, once one action is initiated, I do not believe that it will look for any other events until that action completes.

You can workaround 1) by writing a macro that does everything else itself. However, this requires above average Python programming fu. AutoKey will just launch your macro, but all of the rest is up to you. Python has modules for almost anything a computer can do, so you don't have to reinvent any wheels, but you do have to assemble the car by yourself.

You can workaround 2) by writing a macro which runs something (script or program) as a background task so AutoKey thinks it's done and can go back to minding the store. This also requires programming fu, but in any language you can launch with an exec type command from within a macro.

This second option is a bit more flexible because you don't have to be a Python expert to use it.

There are (at least) two ways to implement this. The simplest would be to launch the script with the macro. You would have to add something else to eventually make it stop.

The other way would be to run a script/program externally from AutoKey. This would be a simple daemon running in the background. Then your macro just has to tell it what to do. There are fancy ways to do things like this with d-bus or named pipes, but the simplest way would be to write a parameter file. The daemon would detect that the parameter file just came into existence or that it has changed and then read it and act accordingly. AutoKey macros could manage the parameter file.

For any of these to work, you need a way to interact with the desktop/applications. The best prebuilt tool for that which I am aware of is xdotool. It can do almost anything you could do from the keyboard and then some. It does have a bit of a learning curve when things happen like an application that opens more than one window and you have to find the right one to talk to or windows are hidden or on different virtual desktops.

Another tool which may help is Xautomation (Xaut). It's kind of like a single-use AutoKey. It's main cool feature is that you can give it an image of something and have it find it on the screen and move your mouse cursor to it. This is great for things that can't be reached with keyboard input alone and for things that do not always display in exactly the same position.

Here, you would be using it externally, but access to it is also built into AutoKey 93.x (autokey-py3).

So, yes, you can do what you want to do. You have a number of powerful tools to help you, but you will have to assemble them them into a solution yourself.

If this hasn't scared you off, we'll be glad to help you on the [support list](https://groups.google.com/forum/#!forum/autokey-users) to figure out the details as you dive into it. We don't have any example code for these sorts of things and would love to add some to our wiki. (If we get into xdotool or other non-AutoKey issues, we'll have to take the discussion off list.)
