See [[Scripting#advanced-scripts]].

Url Displayer
-------------

-  **Author**: `Kreezxil <https://kreezcraft.com>`__
-  **Purpose**: Use a dictionary (associative array) to manage a list of
   urls using short names
-  **Notes**: Great generate links in a chats such as discord or gitter,
   emails and elsewhere

.. code:: python

   packs = {}

   def append(name,url):
       packs[name]=url

   def printUrl(part):
       clipboard.fill_clipboard("{}".format(part))
       time.sleep(0.2)
       keyboard.send_keys("<ctrl>+v<shift>+<enter>")
       time.sleep(0.1)

   append("Sky Client","https://www.curseforge.com/minecraft/modpacks/sky-client")
   append("Skyblock: Godless","https://www.curseforge.com/minecraft/modpacks/skyblock-godless")
   append("Hell Block","https://www.curseforge.com/minecraft/modpacks/hell-block")
   append("Sky Adventure","https://www.curseforge.com/minecraft/modpacks/sky-adventure")
   append("Sky Colony","https://www.curseforge.com/minecraft/modpacks/sky-colony")
   append("Gog Tech","https://www.curseforge.com/minecraft/modpacks/gog-tech")
   append("Binary 6 Squared Sky Challenge","https://www.curseforge.com/minecraft/modpacks/binary-6-squared-sky-challenge")
   append("NSL Mini-Mega Sky Challenge","https://www.curseforge.com/minecraft/modpacks/nsl-mini-mega-sky-challenge")
   append("Kreezcraft Presents Skycraft","https://www.curseforge.com/minecraft/modpacks/kreezcraft-presents-skycraft")
   append("UNFMP Sky Challenge","https://www.curseforge.com/minecraft/modpacks/unfmp-sky-challenge")
   append("Kreezcraft Presents Phantasmagoria","https://www.curseforge.com/minecraft/modpacks/kreezcraft-presents-phantasmagoria")
   append("Philosopher's Life","https://www.curseforge.com/minecraft/modpacks/philosophers-life")
   append("Ultra Mini Omnia","https://www.curseforge.com/minecraft/modpacks/ultra-mini-omnia")

   choices = list(packs.keys())
   choices.sort()
   choices.insert(0,"All")

   retCode, choice = dialog.list_menu( title="Dragon Packs!",options=choices )
   if retCode == 0:
       if choice == "All":
           urls = list(packs.values())
           urls.sort()
           for element in urls:
               printUrl(element)
       else:
           printUrl(packs[choice])
   else:
       exit()

Emoji Speak for chat services such as Discord
---------------------------------------------

-  **Author**: `Kreezxil <https://kreezcraft.com>`__
-  **Purpose**: Use emoji to write a sentence, for instance on Discord.
-  **Notes**: removed the comment and the if statements, decided to go
   100% dictionary lookup method. It is certainly cleaner to look up. It
   feels a bit faster too.
-  **Edited**: 1/28/21 - now even faster!

.. code:: python

   import time
   retCode, phrase = dialog.input_dialog(title='Give me a phrase',message='to make regional?',default='')
   lPhrase = phrase.lower()

   dictionary = {
       "a":":regional_indicator_a:",
       "b":":regional_indicator_b:",
       "c":":regional_indicator_c:",
       "d":":regional_indicator_d:",
       "e":":regional_indicator_e:",
       "f":":regional_indicator_f:",
       "g":":regional_indicator_g:",
       "h":":regional_indicator_h:",
       "i":":regional_indicator_i:",
       "j":":regional_indicator_j:",
       "k":":regional_indicator_k:",
       "l":":regional_indicator_l:",
       "m":":regional_indicator_m:",
       "n":":regional_indicator_n:",
       "o":":regional_indicator_o:",
       "p":":regional_indicator_p:",
       "q":":regional_indicator_q:",
       "r":":regional_indicator_r:",
       "s":":regional_indicator_s:",
       "t":":regional_indicator_t:",
       "u":":regional_indicator_u:",
       "v":":regional_indicator_v:",
       "w":":regional_indicator_w:",
       "x":":regional_indicator_x:",
       "y":":regional_indicator_y:",
       "z":":regional_indicator_z:",
       "0":":zero:",
       "1":":one:",
       "2":":two:",
       "3":":three:",
       "4":":four:",
       "5":":five:",
       "6":":six:",
       "7":":seven:",
       "8":":eight:",
       "9":":nine:",
       "*":":asterisk:",
       "!":":exclamation:",
       "?":":question:",
       "#":":hash:",
       ".":":small_blue_diamond:"
   }

   if retCode == 0:
       exit

   buildPhrase = ""

   for x in lPhrase:
       if  x in dictionary:
           buildPhrase += dictionary[x]
       else:
           buildPhrase += x
       buildPhrase += " "

   clipboard.fill_clipboard(buildPhrase)
   time.sleep(0.2)
   keyboard.send_keys("<ctrl>+v")

Coordinate Calculator similar to `Dinnerbone’s Coordinate Calculator <https://dinnerbone.com/minecraft/tools/coordinates/>`__
-----------------------------------------------------------------------------------------------------------------------------

-  **Porting Author**: `Kreezxil <https://kreezcraft.com>`__
-  **Original Author**: `sebkuip <https://github.com/sebkuip>`__
-  **Original Location**:
   https://github.com/sebkuip/minecraft-region-calculator
-  **Purpose**: Takes x y z coordinates and a type for the coordinates
   given and tells you which region those coordinates are listed in,
   which chunks they are associated with, and the block range associated
   with it.
-  **Notes**: the regex import might not be needed now.
-  **Video**: https://youtu.be/imUh8PCT9f4

.. code:: python

   import re

   def terminate(*args):
       if len(args)>0:
           msg = args[0]
       else:
           msg = "Program Terminated"
       dialog.info_dialog(message=msg)
       exit()

   def validate(data):
       try:
           test=int(data)
           return True
       except:
           return False

   coordType = ["block","chunk","region"]
   coordType.sort()

   retCode, chosenType = dialog.list_menu(options=coordType,title="Type",message="Please choose a coordinate type")
   if retCode:
       terminate()

   retCode, x = dialog.input_dialog(title="X Cord",message="Enter the X coordinate.")
   if retCode:
       terminate()
   if validate(x)==False:
       terminate("X Coord not a valid integer")

   if chosenType=="block":
       retCode, y = dialog.input_dialog(title="Y Coord",message="This coord is pointless, but you may enter it anyways.")
       if retCode:
          terminate()

   retCode, z = dialog.input_dialog(title="Z Coord",message="Enter the Z coordinate.")
   if retCode:
       terminate()
   if validate(z)==False:
       terminate("Z Coord not a valid integer")

   utype = chosenType[0]
   ux = int(x)
   uz = int(z)

   title=f"type: {utype} x: {ux} z: {uz}"

   if utype == "b":
       msg=f"block {ux},{uz} is inside chunk {ux//16},{uz//16} and within region {ux//512},{uz//512}"

   elif utype == "c":
       msg=f"chunk {ux},{uz} contains blocks {ux*16},{uz*16} to {(ux+1)*16-1},{(uz+1)*16-1} and is within region {ux//32},{uz//32}"

   elif utype == "r":
       msg=f"region{ux},{uz} contains blocks {ux*512},{uz*512} to {(ux+1)*512-1},{(uz+1)*512-1} and contains chunks {ux*32},{uz*32} to {(ux+1)*32-1},{(uz+1)*32-1}"

   dialog.info_dialog(title=title,message=msg)

Autoclicker with toggle using Globals
-------------------------------------

-  **Author**: `Kreezxil <https://kreezcraft.com>`__
-  **Purpose**: clicks where the mouse is at, when the script is run
   again, it turns off.

.. code:: python

   x = store.get_global_value("clicker_status")

   if x == "on":
       #turn it off if it is on
       store.set_global_value("clicker_status","off")

   else:
       #any other value is considered off, should cover nulls
       store.set_global_value("clicker_status","on")

   while True:
       time.sleep(0.1)
       mouse.click_relative_self(0,0,1)
       x = store.get_global_value("clicker_status")
       if x == "off":
           #leave the execution if we've been toggled off
           break
