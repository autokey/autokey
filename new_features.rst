Click on an area that can be identified with an image
=====================================================

Requires `xautomation`_ and `ImageMagick®`_ to be installed.

.. _xautomation: http://hoopajoo.net/projects/xautomation.html
.. _ImageMagick®: http://www.imagemagick.org/

.. code:: python

   hl = highlevel
   LEFT = hl.LEFT; MIDDLE = hl.MIDDLE; RIGHT = hl.RIGHT
   click_on_pat = hl.click_on_pat

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
    
   # left click of top left of the pattern
   click_on_pat("pat.png",LEFT,(0,0))
    
   # left click of bottom right of the pattern
   click_on_pat("pat.png",1,(100,100))
    
   try:
       click_on_pat("pat1.png")
   except PatternNotFound:
       print("Pattern not found")



Running AutoKey scripts on a interpreter
========================================

We use autokey-gtk as the launcher. If you are using autokey-qt, replace “-gtk” with “-qt”.

1. start the autokey launcher autokey-gtk.
2. run the launcher with the interpreter. The main window will show up, close it or switch back to the interpreter.

.. code:: sh

   python3 -i `which autokey-gtk`

3. Then run the following in the interpreter. Currently, not all functions can be used.

.. code:: python

   import autokey.scripting
   system = autokey.scripting.System()
   hl = autokey.scripting.highlevel

test it:

.. code:: python

   system.exec_command('ls')
   hl.click_on_pat("pattern.png")

