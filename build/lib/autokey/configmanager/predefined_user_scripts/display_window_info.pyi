# Displays the information of the next window to be left-clicked
import time
mouse.wait_for_click(5)
time.sleep(0.2)
window_title = window.get_active_title()
window_class = window.get_active_class()

dialog.info_dialog(
    "Window information",
    "Active window information:\nTitle: '{}'\nClass: '{}'".format(window_title, window_class)
)
