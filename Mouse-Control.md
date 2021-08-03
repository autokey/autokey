# Control the Mouse with AutoKey
The computer's mouse can be used in scripts in a variety of ways. You can perform clicks by sending them relative to the screen, relative to the active window, or relative to the mouse's current position.

## Table of Contents
  * [Before you begin](#before-you-begin)
    * [Get the current mouse coordinates](#get-the-current-mouse-coordinates)
  * [Sending mouse clicks](#sending-mouse-clicks)
    * [Send a mouse click relative to the active window](#send-a-mouse-click-relative-to-the-active-window)
    * [Send a mouse-click relative to the mouse's current position](#send-a-mouse-click-relative-to-the-mouses-current-position)
    * [Send a mouse click relative to the screen](#send-a-mouse-click-relative-to-the-screen)
  * [Wait for a mouse click](#wait-for-a-mouse-click)
  * [Press and hold a mouse button](#press-and-hold-a-mouse-button)
  * [See also](#see-also)

************************************************************************
## Before you begin

### Get the current mouse coordinates
This script, from Sam Sebastian, displays the current mouse coordinates in a pop-up dialog:
```python
from Xlib import X, display # import the necessary classes from the specified module
d = display.Display().screen().root.query_pointer() # get pointer location
x = str(d.root_x) # get x coord and convert to string
y = str(d.root_y) # get y coord and convert to string
dialog.info_dialog("(X, Y)", x+", "+y) # create an info dialog to display the coordinates
```

## Sending mouse clicks

### Send a mouse click relative to the active window
```
mouse.click_relative(x, y, button)
```
* The x is the x-coordinate in pixels from the left on the horizontal axis relative to the upper left corner of the active window
* The y is the y-coordinate in pixels from the top on the vertical axis relative to the upper left corner of the active window.
* The button is the kind of mouse button to emulate (1, 2, or 3 to represent left, middle, or right, accepting up to 9 buttons for fancy mice).

Example: Send a left-click to the active window:
```python
mouse.click_relative(10, 20, 1)
```
Example: Send a middle-click to the active window:
```python
mouse.click_relative(10, 20, 2)
```
Example: Send a right-click to the active window:
```python
mouse.click_relative(10, 20, 3)
```

### Send a mouse-click relative to the mouse's current position
```python
mouse.click_relative_self(x, y, button)
```
* The x is the x-coordinate in pixels from the left on the horizontal axis relative to the mouse's current position.
* The y is the y-coordinate in pixels from the top on the vertical axis relative to the mouse's current position.
* The button is the kind of mouse button to emulate (1, 2, or 3 to represent left, middle, or right, accepting up to 9 buttons for fancy mice).

Example: Send a left-click at the mouse's current location:
```python
mouse.click_relative_self(0, 0, 1)
```
Example: Send a middle-click at the mouse's current location:
```python
mouse.click_relative_self(0, 0, 2)
```
Example: Send a right-click at the mouse's current location:
```python
mouse.click_relative_self(0, 0, 3)
```
Example: Send a left-click 20 pixels to the right and 100 pixels down from the mouse's current location:
```python
mouse.click_relative_self(20, 100, 1)
```
Example: Send a left-click 20 pixels to the left and 100 pixels down from the mouse's current location:
```python
mouse.click_relative_self(-20, 100, 1)
```

### Send a mouse click relative to the screen
```python
mouse.click_absolute(x, y, button)
```
* The x is the x-coordinate in pixels from the left on the horizontal axis relative to the upper left corner of the screen.
* The y is the y-coordinate in pixels from the top on the vertical axis relative to the upper left corner of the screen.
* The button is the kind of mouse button to emulate (1, 2, or 3 to represent left, middle, or right, accepting up to 9 buttons for fancy mice).

Example: Send a left-click relative to the screen:
```python
mouse.click_absolute(20, 40, 1)
```
Example: Send a middle-click relative to the screen:
```python
mouse.click_absolute(20, 40, 2)
```
Example: Send a right-click relative to the screen:
```python
mouse.click_absolute(20, 40, 3)
```

************************************************************************

## Wait for a mouse click

You can make a script wait for a mouse click, either with a timer that will perform the action after the specified delay if no mouse-click has been received or without a timer, in which case the action will only be performed once the mouse is actually clicked.

Example: Wait for left-click before printing the text:
```python
mouse.wait_for_click(1)
keyboard.send_keys("hello world")
```
Example: Wait for middle-click before printing the text:
```python
mouse.wait_for_click(2)
keyboard.send_keys("hello world")
```
Example: Wait for left-click before printing the text or print it when the timer runs out if no left-click occurs:
```python
mouse.wait_for_click(1, timeOut=3.0)
keyboard.send_keys("hello world")
```

************************************************************************

## Press and hold a mouse button

This is not implemented in AutoKey yet, but there are some work-arounds:
* Someone on this **Ask Ubuntu** page re-bound the mouse button as a work-around: [https://askubuntu.com/questions/1223158/how-do-i-hold-down-left-click-in-autokey](https://askubuntu.com/questions/1223158/how-do-i-hold-down-left-click-in-autokey)
* Someone on this **Ask Ubuntu** page suggested that you would need more low-level tools than AutoKey to accomplish this: [https://askubuntu.com/questions/1104340/autokey-question-how-can-i-hold-down-a-simulated-keypress-while-holding-down-th](https://askubuntu.com/questions/1104340/autokey-question-how-can-i-hold-down-a-simulated-keypress-while-holding-down-th)
* Someone on this **GitHub** page remapped the Z key to the left mouse button as a work-around: [https://github.com/autokey/autokey/issues/243](https://github.com/autokey/autokey/issues/243)
* Another person on the same GitHub page suggested this as a work-around if you have xdotool installed (note that you need to click the mouse button again to turn it off):
```python
import subprocess
subprocess.run(["xdotool", "mousedown", "1"])
```

************************************************************************

## See also
* There are some mouse examples that inspired the examples above on the "API Examples" page in the AutoKey wiki: [https://github.com/autokey/autokey/wiki/API-Examples#mouse](https://github.com/autokey/autokey/wiki/API-Examples#mouse)
* There are also details on this GitHub page under the mouse class: [https://autokey.github.io/](https://autokey.github.io/)

************************************************************************
