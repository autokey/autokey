import autokey.model.folder
import autokey.model.helpers
import autokey.model.phrase
import autokey.model.script

def delete_hotkeys(app, removed_item):
    if autokey.model.helpers.TriggerMode.HOTKEY in removed_item.modes:
        app.hotkey_removed(removed_item)

    if isinstance(removed_item, autokey.model.folder.Folder):
        for subFolder in removed_item.folders:
            delete_hotkeys(app, subFolder)

        for item in removed_item.items:
            if autokey.model.helpers.TriggerMode.HOTKEY in item.modes:
                app.hotkey_removed(item)
