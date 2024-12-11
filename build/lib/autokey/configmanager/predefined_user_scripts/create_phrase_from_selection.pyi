# Create a new phrase from the currently selected text, without having any abbreviation or hotkey assigned.
contents = clipboard.get_selection()
if len(contents) > 20:
    # The title is abbreviated, if it is longer than 20 characters
    title = contents[0:19] + "…"
else:
    title = contents
folder = engine.get_folder("My Phrases")  # The phrase will be created in this folder.
engine.create_phrase(folder, title, contents)
