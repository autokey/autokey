text = clipboard.get_selection()
keyboard.send_key("<delete>")
keyboard.send_keys("The text {} was here previously".format(text))
