* Author: [Kreezxil](https://kreezcraft.com)
* Description: Allows to create a recipe automatically for use with [The Kabbalah Block](https://www.curseforge.com/minecraft/mc-mods/the-kabbalah-block) Mod where Extended Crafting mod is also available.
* License: MIT
```python
retCode, userInput = dialog.input_dialog(title='Kabbalah Keys',
	message='Enter the name of the thing being created, e.g. minecraft:dirt', 
	default='')

if retCode:
	myMessage = 'Dialog exit code was: ' + str(retCode)
	dialog.info_dialog(title='You cancelled the dialog', 
	message=myMessage, width='200') # width is extra zenity parameter 
else:
	
	temp = userInput
	recipeResult = temp
	tableType="minecraft:crafting_shaped"
	if len(userInput)>9:
		tableType="extendedcrafting:shaped_table"
		userInput="{:<81}".format(temp)
	else:
		userInput="{:<9}".format(temp)
		
	keyboard.send_keys("{ <enter>")
	keyboard.send_keys("\"type\": \"{}\",<enter>".format(tableType))
	keyboard.send_keys("\"pattern\": [<enter>")
	if tableType == "minecraft:crafting_shaped":
		x = 3
	else: 
		x = 9
		
	index=0
	grid=userInput
	for i in range(x):
		keyboard.send_keys("\"")
		for j in range(x):
			keyboard.send_keys(grid[index])
			index=index+1
		keyboard.send_keys("\"")
		if tableType == "minecraft:crafting_shaped" and index == 9:
			keyboard.send_keys("<enter>")
		elif tableType == "extendedcrafting:shaped_table" and index == 81:
			keyboard.send_keys("<enter>")
		else:
			keyboard.send_keys(",<enter>")
		
	keyboard.send_keys("],<enter>")
	keyboard.send_keys("\"key\": {<enter>")
			
	
	keys = sorted(set(list(recipeResult)))
	index=0
	for element in keys:
		index=index+1
		if element == "_":
			element = "underscore"
		elif element == ":":
			element = "colon"
		keyboard.send_keys("\""+element+"\": { \"item\": \"thekabbalahblock:letter_"+element+"\" }")
		if index == len(keys):
			keyboard.send_keys("<enter>")
		else:
			keyboard.send_keys(",<enter>")
        
keyboard.send_keys("},<enter>\"result\": {<enter>\"item\": \""+recipeResult+"\"<enter>}<enter>}")

```