choices = ["something", "something else", "a third thing"]

return_code, choice = dialog.list_menu(choices)
if not return_code:  # return code is 0 (thus false) on success.
    keyboard.send_keys("You chose " + choice)
