============
New features
============
This page documents new features built on top of the Python 3 port of the original AutoKey.

.. contents::

Acknowledge Gnome 3 notifications
=================================

Moves mouse pointer to the bottom center of the screen and clicks on it.

.. code:: python

   acknowledge_gnome_notification()


Click on or move pointer to an area that can be identified with an image
========================================================================
Requires `xautomation`_ and `ImageMagick®`_ to be installed.

.. _xautomation: http://hoopajoo.net/projects/xautomation.html
.. _ImageMagick®: http://www.imagemagick.org/

`Source code`_.

.. _Source code: https://github.com/autokey/autokey/blob/master/src/lib/scripting_highlevel.py

.. code:: python

   # click_on_pat(pat:str, mousebutton:int=1, offset:(float,float)=None, tolerance:int=0, restore_pos:bool = False) -> None
   # move_to_pat(pat:str, offset:(float,float)=None, tolerance:int=0)

   hl = highlevel
   LEFT = hl.LEFT; MIDDLE = hl.MIDDLE; RIGHT = hl.RIGHT
   click_on_pat = hl.click_on_pat
   move_to_pat = hl.move_to_pat
   PatternNotFound = hl.PatternNotFound
   # or use
   # from autokey.scripting_highlevel import *
   # to import all functions

   click_on_pat("pattern.png")

   # left click on centre of pattern
   click_on_pat("pat.png",1)
   click_on_pat("pat.png",LEFT)

   # middle click on centre of pattern
   click_on_pat("pat.png",2)
   click_on_pat("pat.png",MIDDLE)

   # right click on centre of pattern
   click_on_pat("pat.png",3)
   click_on_pat("pat.png",RIGHT)

   # left click of top left of the pattern and return to the original mouse position after clicking.
   click_on_pat("pat.png",LEFT,(0,0), restore_pos=True)

   # left click of bottom right of the pattern, with tolerance for “fuzzy” matches set to 1.
   click_on_pat("pat.png",1,(100,100),1)

   try:
       click_on_pat("pat1.png")
   except PatternNotFound:
       print("Pattern not found")



Running AutoKey scripts interactively on a shell
================================================

Start “autokey-shell”. Currently, only functions from “system” and “highlevel” modules are exported to the shell.

In the shell you can use functions provided by AutoKey:

.. code:: python

   print(system.exec_command('ls'))
   help(hl.click_on_pat)
   help(hl.visgrep)
   hl.click_on_pat("pattern.png")
