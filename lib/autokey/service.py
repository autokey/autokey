#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Chris Dekter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import traceback
import collections
import time
import logging

from autokey import common
from autokey.iomediator.key import Key, KEY_FIND_RE
from autokey.iomediator import IoMediator

from .macro import MacroManager

from . import scripting, model, scripting_Store, scripting_highlevel
from .configmanager import ConfigManager, SERVICE_RUNNING, SCRIPT_GLOBALS, save_config, UNDO_USING_BACKSPACE
import threading
logger = logging.getLogger("service")

MAX_STACK_LENGTH = 150


def threaded(f):

    def wrapper(*args):
        t = threading.Thread(target=f, args=args, name="Phrase-thread")
        t.setDaemon(False)
        t.start()

    wrapper.__name__ = f.__name__
    wrapper.__dict__ = f.__dict__
    wrapper.__doc__ = f.__doc__
    return wrapper

def synchronized(lock):
    """ Synchronization decorator. """

    def wrap(f):
        def new_function(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        return new_function
    return wrap


class Service:
    """
    Handles general functionality and dispatching of results down to the correct
    execution service (phrase or script).
    """

    def __init__(self, app):
        logger.info("Starting service")
        self.configManager = app.configManager
        ConfigManager.SETTINGS[SERVICE_RUNNING] = False
        self.mediator = None
        self.app = app
        self.inputStack = collections.deque(maxlen=MAX_STACK_LENGTH)
        self.lastStackState = ''
        self.lastMenu = None

    def start(self):
        self.mediator = IoMediator(self)
        self.mediator.interface.initialise()
        self.mediator.interface.start()
        self.mediator.start()
        ConfigManager.SETTINGS[SERVICE_RUNNING] = True
        self.scriptRunner = ScriptRunner(self.mediator, self.app)
        self.phraseRunner = PhraseRunner(self)
        scripting_Store.Store.GLOBALS = ConfigManager.SETTINGS[SCRIPT_GLOBALS]
        logger.info("Service now marked as running")

    def unpause(self):
        ConfigManager.SETTINGS[SERVICE_RUNNING] = True
        logger.info("Unpausing - service now marked as running")

    def pause(self):
        ConfigManager.SETTINGS[SERVICE_RUNNING] = False
        logger.info("Pausing - service now marked as stopped")

    def is_running(self):
        return ConfigManager.SETTINGS[SERVICE_RUNNING]

    def shutdown(self, save=True):
        logger.info("Service shutting down")
        if self.mediator is not None: self.mediator.shutdown()
        if save:
            save_config(self.configManager)
        logger.debug("Service shutdown completed.")

    def handle_mouseclick(self, rootX, rootY, relX, relY, button, windowTitle):
        # logger.debug("Received mouse click - resetting buffer")
        self.inputStack.clear()

        # If we had a menu and receive a mouse click, means we already
        # hid the menu. Don't need to do it again
        self.lastMenu = None

        # Clear last to prevent undo of previous phrase in unexpected places
        self.phraseRunner.clear_last()

    def handle_keypress(self, rawKey, modifiers, key, window_info):
        logger.debug("Raw key: %r, modifiers: %r, Key: %s", rawKey, modifiers, key)
        logger.debug("Window visible title: %r, Window class: %r" % window_info)
        self.configManager.lock.acquire()

        # Always check global hotkeys
        for hotkey in self.configManager.globalHotkeys:
            hotkey.check_hotkey(modifiers, rawKey, window_info)

        if self.__shouldProcess(window_info):
            itemMatch = None
            menu = None

            for item in self.configManager.hotKeys:
                if item.check_hotkey(modifiers, rawKey, window_info):
                    itemMatch = item
                    break

            if itemMatch is not None:
                logger.info('Matched {} "{}" with hotkey and prompt={}'.format(
                    itemMatch.__class__.__name__, itemMatch.description, itemMatch.prompt
                ))
                if itemMatch.prompt:
                    menu = ([], [itemMatch])

            else:
                for folder in self.configManager.hotKeyFolders:
                    if folder.check_hotkey(modifiers, rawKey, window_info):
                        #menu = PopupMenu(self, [folder], [])
                        menu = ([folder], [])


            if menu is not None:
                logger.debug("Matched Folder with hotkey - showing menu")
                if self.lastMenu is not None:
                    #self.lastMenu.remove_from_desktop()
                    self.app.hide_menu()
                self.lastStackState = ''
                self.lastMenu = menu
                #self.lastMenu.show_on_desktop()
                self.app.show_popup_menu(*menu)

            if itemMatch is not None:
                self.__tryReleaseLock()
                self.__processItem(itemMatch)


            ### --- end of hotkey processing --- ###

            modifierCount = len(modifiers)

            if modifierCount > 1 or (modifierCount == 1 and Key.SHIFT not in modifiers):
                self.inputStack.clear()
                self.__tryReleaseLock()
                return

            ### --- end of processing if non-printing modifiers are on --- ###

            if self.__updateStack(key):
                currentInput = ''.join(self.inputStack)
                item, menu = self.__checkTextMatches([], self.configManager.abbreviations,
                                                    currentInput, window_info, True)
                if not item or menu:
                    item, menu = self.__checkTextMatches(
                        self.configManager.allFolders,
                        self.configManager.allItems,
                        currentInput, window_info)  # type: model.Phrase, list

                if item:
                    self.__tryReleaseLock()
                    logger.info('Matched {} "{}" having abbreviations "{}" against current input'.format(
                        item.__class__.__name__, item.description, item.abbreviations))
                    self.__processItem(item, currentInput)
                elif menu:
                    if self.lastMenu is not None:
                        #self.lastMenu.remove_from_desktop()
                        self.app.hide_menu()
                    self.lastMenu = menu
                    #self.lastMenu.show_on_desktop()
                    self.app.show_popup_menu(*menu)

                logger.debug("Input queue at end of handle_keypress: %s", self.inputStack)

        self.__tryReleaseLock()

    def __tryReleaseLock(self):
        try:
            self.configManager.lock.release()
        except:
            logger.exception("Ignored locking error in handle_keypress")

    def run_folder(self, name):
        folder = None
        for f in self.configManager.allFolders:
            if f.title == name:
                folder = f

        if folder is None:
            raise Exception("No folder found with name '%s'" % name)

        self.app.show_popup_menu([folder])


    def run_phrase(self, name):
        phrase = self.__findItem(name, model.Phrase, "phrase")
        self.phraseRunner.execute(phrase)

    def run_script(self, name):
        script = self.__findItem(name, model.Script, "script")
        self.scriptRunner.execute(script)

    def __findItem(self, name, objType, typeDescription):
        for item in self.configManager.allItems:
            if item.description == name and isinstance(item, objType):
                return item

        raise Exception("No %s found with name '%s'" % (typeDescription, name))

    @threaded
    def item_selected(self, item):
        time.sleep(0.25) # wait for window to be active
        self.lastMenu = None # if an item has been selected, the menu has been hidden
        self.__processItem(item, self.lastStackState)

    def calculate_extra_keys(self, buffer):
        """
        Determine extra keys pressed since the given buffer was built
        """
        extraBs = len(self.inputStack) - len(buffer)
        if extraBs > 0:
            extraKeys = ''.join(self.inputStack[len(buffer)])
        else:
            extraBs = 0
            extraKeys = ''
        return extraBs, extraKeys

    def __updateStack(self, key):
        """
        Update the input stack in non-hotkey mode, and determine if anything
        further is needed.

        @return: True if further action is needed
        """
        #if self.lastMenu is not None:
        #    if not ConfigManager.SETTINGS[MENU_TAKES_FOCUS]:
        #        self.app.hide_menu()
        #
        #    self.lastMenu = None

        if key == Key.ENTER:
            # Special case - map Enter to \n
            key = '\n'
        if key == Key.TAB:
            # Special case - map Tab to \t
            key = '\t'

        if key == Key.BACKSPACE:
            if ConfigManager.SETTINGS[UNDO_USING_BACKSPACE] and self.phraseRunner.can_undo():
                self.phraseRunner.undo_expansion()
            else:
                # handle backspace by dropping the last saved character
                try:
                    self.inputStack.pop()
                except IndexError:
                    # in case self.inputStack is empty
                    pass

            return False

        elif len(key) > 1:
            # non-simple key
            self.inputStack.clear()
            self.phraseRunner.clear_last()
            return False
        else:
            # Key is a character
            self.phraseRunner.clear_last()
            # if len(self.inputStack) == MAX_STACK_LENGTH, front items will removed for appending new items.
            self.inputStack.append(key)
            return True

    def __checkTextMatches(self, folders, items, buffer, windowInfo, immediate=False):
        """
        Check for an abbreviation/predictive match among the given folder and items
        (scripts, phrases).

        @return: a tuple possibly containing an item to execute, or a menu to show
        """
        itemMatches = []
        folderMatches = []

        for item in items:
            if item.check_input(buffer, windowInfo):
                if not item.prompt and immediate:
                    return item, None
                else:
                    itemMatches.append(item)

        for folder in folders:
            if folder.check_input(buffer, windowInfo):
                folderMatches.append(folder)
                break # There should never be more than one folder match anyway

        if self.__menuRequired(folderMatches, itemMatches, buffer):
            self.lastStackState = buffer
            #return (None, PopupMenu(self, folderMatches, itemMatches))
            return None, (folderMatches, itemMatches)
        elif len(itemMatches) == 1:
            self.lastStackState = buffer
            return itemMatches[0], None
        else:
            return None, None


    def __shouldProcess(self, windowInfo):
        """
        Return a boolean indicating whether we should take any action on the keypress
        """
        return windowInfo[0] != "Set Abbreviations" and self.is_running()

    def __processItem(self, item, buffer=''):
        self.inputStack.clear()
        self.lastStackState = ''

        if isinstance(item, model.Phrase):
            self.phraseRunner.execute(item, buffer)
        else:
            self.scriptRunner.execute(item, buffer)



    def __haveMatch(self, data):
        folder_match, item_matches = data
        if folder_match is not None:
            return True
        if len(item_matches) > 0:
            return True

        return False

    def __menuRequired(self, folders, items, buffer):
        """
        @return: a boolean indicating whether a menu is needed to allow the user to choose
        """
        if len(folders) > 0:
            # Folders always need a menu
            return True
        if len(items) == 1:
            return items[0].should_prompt(buffer)
        elif len(items) > 1:
            # More than one 'item' (phrase/script) needs a menu
            return True

        return False


class PhraseRunner:

    def __init__(self, service: Service):
        self.service = service
        self.macroManager = MacroManager(service.scriptRunner.engine)
        self.lastExpansion = None
        self.lastPhrase = None
        self.lastBuffer = None
        self.contains_special_keys = False

    @threaded
    #@synchronized(iomediator.SEND_LOCK)
    def execute(self, phrase: model.Phrase, buffer=''):
        mediator = self.service.mediator  # type: IoMediator
        mediator.interface.begin_send()
        try:
            expansion = phrase.build_phrase(buffer)
            self.macroManager.process_expansion(expansion)

            self.contains_special_keys = self.phrase_contains_special_keys(expansion)
            mediator.send_backspace(expansion.backspaces)
            if phrase.sendMode == model.SendMode.KEYBOARD:
                mediator.send_string(expansion.string)
            else:
                mediator.paste_string(expansion.string, phrase.sendMode)

            self.lastExpansion = expansion
            self.lastPhrase = phrase
            self.lastBuffer = buffer
        finally:
            mediator.interface.finish_send()

    def can_undo(self):
        can_undo = self.lastExpansion is not None and not self.phrase_contains_special_keys(self.lastExpansion)
        logger.debug("Undoing last phrase expansion requested. Can undo last expansion: {}".format(can_undo))
        return can_undo

    @staticmethod
    def phrase_contains_special_keys(expansion: model.Expansion) -> bool:
        """
        Determine if the expansion contains any special keys, including those resulting from any processed macros
        (<script>, <file>, etc). If any are found, the phrase cannot be undone.

        Python Zen: »In the face of ambiguity, refuse the temptation to guess.«
        The question 'What does the phrase expansion "<ctrl>+a<shift>+<insert>" do?' cannot be answered. Because the key
        bindings cannot be assumed to result in the actions "select all text, then replace with clipboard content",
        the undo operation can not be performed. Thus always disable undo, when special keys are found.
        """
        found_special_keys = KEY_FIND_RE.findall(expansion.string.lower())
        return bool(found_special_keys)

    def clear_last(self):
        self.lastExpansion = None
        self.lastPhrase = None

    # @synchronized(iomediator.SEND_LOCK) #TODO_PY3 commented this
    def undo_expansion(self):
        logger.info("Undoing last phrase expansion")
        replay = self.lastPhrase.get_trigger_chars(self.lastBuffer)
        logger.debug("Replay string: %s", replay)
        logger.debug("Erase string: %r", self.lastExpansion.string)
        mediator = self.service.mediator  # type: IoMediator

        #mediator.send_right(self.lastExpansion.lefts)
        mediator.interface.begin_send()
        try:
            mediator.remove_string(self.lastExpansion.string)
            mediator.send_string(replay)
            self.clear_last()
        finally:
            mediator.interface.finish_send()


class ScriptRunner:

    def __init__(self, mediator: IoMediator, app):
        self.mediator = mediator
        self.app = app
        self.error = ''
        self.scope = globals()
        self.scope["highlevel"] = scripting_highlevel
        self.scope["keyboard"] = scripting.Keyboard(mediator)
        self.scope["mouse"] = scripting.Mouse(mediator)
        self.scope["system"] = scripting.System()
        self.scope["window"] = scripting.Window(mediator)
        self.scope["engine"] = scripting.Engine(app.configManager, self)

        if common.USING_QT:
            self.scope["dialog"] = scripting.QtDialog()
            self.scope["clipboard"] = scripting.QtClipboard(app)
        else:
            self.scope["dialog"] = scripting.GtkDialog()
            self.scope["clipboard"] = scripting.GtkClipboard(app)

        self.engine = self.scope["engine"]

    @threaded
    def execute(self, script: model.Script, buffer=''):
        logger.debug("Script runner executing: %r", script)

        scope = self.scope.copy()
        scope["store"] = script.store

        backspaces, stringAfter = script.process_buffer(buffer)
        self.mediator.send_backspace(backspaces)
        if script.path is not None:
            # Overwrite __file__ to contain the path to the user script instead of the path to this service.py file.
            scope["__file__"] = script.path
        try:
            exec(script.code, scope)
        except Exception as e:
            logger.exception("Script error")
            self.error = "Script name: '{}'\n{}".format(script.description, traceback.format_exc())
            self.app.notify_error("The script '{}' encountered an error".format(script.description))

        self.mediator.send_string(stringAfter)

    def run_subscript(self, script):
        scope = self.scope.copy()
        scope["store"] = script.store
        exec(script.code, scope)
