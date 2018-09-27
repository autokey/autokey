# Create a new Phrase from the current text selection. Ask for an abbreviation and then create a new Phrase having
# this abbreviation assigned.
import time
time.sleep(0.25)
contents = clipboard.get_selection()
return_code, abbreviation = dialog.input_dialog("New Abbreviation", "Choose an abbreviation for the new phrase")
if not return_code:  # return code is 0 (thus false) on success.
    if len(contents) > 20:
        title = contents[0:19] + "…"
    else:
        title = contents
    folder = engine.get_folder("My Phrases")
    engine.create_abbreviation(folder, title, abbreviation, contents)
