============
New features
============
This page documents new features built on top of the Python 3 port of the original AutoKey.

.. contents::

Click on an area that can be identified with an image
=====================================================
Requires `xautomation`_ and `ImageMagick®`_ to be installed.

.. _xautomation: http://hoopajoo.net/projects/xautomation.html
.. _ImageMagick®: http://www.imagemagick.org/

`Source code`_.

.. _Source code: https://github.com/guoci/autokey-py3/blob/master/src/lib/scripting_highlevel.py

.. code:: python

   click_on_pat(pat:str, mousebutton:int=1, offset:(float,float)=None, tolerance:int=0, restore_pos:bool = False) -> None
   
   hl = highlevel
   LEFT = hl.LEFT; MIDDLE = hl.MIDDLE; RIGHT = hl.RIGHT
   click_on_pat = hl.click_on_pat
   PatternNotFound = hl.PatternNotFound

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



Running AutoKey scripts on an interpreter
=========================================

We use autokey-gtk as the launcher. If you are using autokey-qt, replace “-gtk” with “-qt”.

1. Start the autokey launcher autokey-gtk.
2. Run the launcher with the interpreter. The main window will show up, close it or switch back to the interpreter.

.. code:: sh

   python3 -i `which autokey-gtk`

3. Then run the following in the interpreter. Currently, not all functions can be used.

.. code:: python

   import autokey.scripting
   system = autokey.scripting.System()
   hl = autokey.scripting.highlevel

Test some functions provided by AutoKey-Py3:

.. code:: python

   system.exec_command('ls')
   help(hl.click_on_pat)
   help(hl.visgrep)
   hl.click_on_pat("pattern.png")

