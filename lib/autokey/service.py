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


import collections
import datetime
import pathlib
import threading
import time
import traceback
import typing

import autokey.model
import autokey.model.phrase
import autokey.model.script
import autokey.model.store
from autokey.model.key import Key, KEY_FIND_RE
from autokey.iomediator.iomediator import IoMediator

from autokey.macro import MacroManager

import autokey.scripting
from autokey.configmanager.configmanager import ConfigManager, save_config
import autokey.configmanager.configmanager_constants as cm_constants

logger = __import__("autokey.logger").logger.get_logger(__name__)
MAX_STACK_LENGTH = 150


def threaded(f):

    def wrapper(*args, **kwargs):
        t = threading.Thread(target=f, args=args, kwargs=kwargs, name="Phrase-thread")
        t.setDaemon(False)
        t.start()

    wrapper.__name__ = f.__name__
    wrapper.__dict__ = f.__dict__
    wrapper.__doc__ = f.__doc__
    wrapper._original = f  # Store the original function for unit testing purposes.
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
        ConfigManager.SETTINGS[cm_constants.SERVICE_RUNNING] = False
        self.mediator = None
        self.app = app
        self.inputStack = collections.deque(maxlen=MAX_STACK_LENGTH)
        self.lastStackState = ''
        self.lastMenu = None
        self.name = None

    def start(self):
        self.mediator = IoMediator(self)
        self.mediator.interface.initialise()
        self.mediator.interface.start()
        self.mediator.start()
        ConfigManager.SETTINGS[cm_constants.SERVICE_RUNNING] = True
        self.scriptRunner = ScriptRunner(self.mediator, self.app)
        self.phraseRunner = PhraseRunner(self)
        autokey.model.store.Store.GLOBALS.update(ConfigManager.SETTINGS[cm_constants.SCRIPT_GLOBALS])
        logger.info("Service now marked as running")

    def unpause(self):
        ConfigManager.SETTINGS[cm_constants.SERVICE_RUNNING] = True
        logger.info("Unpausing - service now marked as running")

    def pause(self):
        ConfigManager.SETTINGS[cm_constants.SERVICE_RUNNING] = False
        logger.info("Pausing - service now marked as stopped")

    def is_running(self):
        return ConfigManager.SETTINGS[cm_constants.SERVICE_RUNNING]

    def shutdown(self, save=True):
        logger.info("Service shutting down")
        if self.mediator is not None: self.mediator.shutdown()
        if save:
            save_config(self.configManager)
        logger.debug("Service shutdown completed.")

    def handle_mouseclick(self, rootX, rootY, relX, relY, button, windowTitle):
        # logger.debug("Received mouse click - resetting buffer")
        self.inputStack.clear()

        logger.log(level=9, msg="Mouse click at root:("+str(rootX)+", "+str(rootY)+") Relative:("+str(relX)+","+str(relY)+") Button: "+str(button)+" In window: "+str(windowTitle))
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
                        currentInput, window_info)  # type: autokey.model.phrase.Phrase, list

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
            if self.configManager.lock.locked():
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
        phrase = self.__findItem(name, autokey.model.phrase.Phrase, "phrase")
        self.phraseRunner.execute(phrase)

    def run_script(self, name):
        path = pathlib.Path(name)
        path = path.expanduser()
        # Check if absolute path.
        if pathlib.PurePath(path).is_absolute() and path.exists():
            self.scriptRunner.execute_path(path)
        else:
            script = self.__findItem(name, autokey.model.script.Script, "script")
            self.scriptRunner.execute_script(script)

    def __findItem(self, name, objType, typeDescription):
        for item in self.configManager.allItems:
            if item.description == name and isinstance(item, objType):
                return item

        raise Exception("No %s found with name '%s'" % (typeDescription, name))

    @threaded
    def item_selected(self, item):
        time.sleep(0.25)  # wait for window to be active
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
            if ConfigManager.SETTINGS[cm_constants.UNDO_USING_BACKSPACE] and self.phraseRunner.can_undo():
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

        if isinstance(item, autokey.model.phrase.Phrase):
            self.phraseRunner.execute(item, buffer)
        else:
            self.scriptRunner.execute_script(item, buffer)



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
    def execute(self, phrase: autokey.model.phrase.Phrase, buffer=''):
        mediator = self.service.mediator  # type: IoMediator
        mediator.interface.begin_send()
        try:
            expansion = phrase.build_phrase(buffer)
            expansion.string = \
                    self.macroManager.process_expansion_macros(expansion.string)

            self.contains_special_keys = self.phrase_contains_special_keys(expansion)
            mediator.send_backspace(expansion.backspaces)
            if phrase.sendMode == autokey.model.phrase.SendMode.KEYBOARD:
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
    def phrase_contains_special_keys(expansion: autokey.model.phrase.Expansion) -> bool:
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
        self.error_records = []  # type: typing.List[autokey.model.ScriptErrorRecord]
        self.scope = globals()
        self.scope["highlevel"] = autokey.scripting.highlevel
        self.scope["keyboard"] = autokey.scripting.Keyboard(mediator)
        self.scope["mouse"] = autokey.scripting.Mouse(mediator)
        self.scope["system"] = autokey.scripting.System()
        self.scope["window"] = autokey.scripting.Window(mediator)
        self.scope["engine"] = autokey.scripting.Engine(app.configManager, self)

        self.scope["dialog"] = autokey.scripting.Dialog()
        self.scope["clipboard"] = autokey.scripting.Clipboard(app)

        self.engine = self.scope["engine"]

    def clear_error_records(self):
        self.error_records.clear()

    @threaded
    def execute_script(self, script: autokey.model.script.Script, buffer=''):
        logger.debug("Script runner executing: %r", script)

        scope = self.scope.copy()
        scope["store"] = script.store

        backspaces, trigger_character = script.process_buffer(buffer)
        self.mediator.send_backspace(backspaces)

        self._set_triggered_abbreviation(scope, buffer, trigger_character)
        if script.path is not None:
            # Overwrite __file__ to contain the path to the user script instead of the path to this service.py file.
            scope["__file__"] = script.path
        self._execute(scope, script)

        self.mediator.send_string(trigger_character)

    @threaded
    def execute_path(self, path: pathlib.Path):
        logger.debug("Script runner executing: {}".format(path))
        scope = self.scope.copy()
        # Overwrite __file__ to contain the path to the user script instead of the path to this service.py file.
        scope["__file__"] = str(path.resolve())
        self._execute(scope, path)

    def _record_error(self, script: typing.Union[autokey.model.script.Script, pathlib.Path], start_time: time.time):
        error_time = datetime.datetime.now().time()
        logger.exception("Script error")
        traceback_str = traceback.format_exc()
        error_record = autokey.model.script.ScriptErrorRecord(
                script=script, error_traceback=traceback_str, start_time=start_time, error_time=error_time
        )
        self.error_records.append(error_record)
        self.app.notify_error(error_record)

    def _execute(self, scope, script: typing.Union[autokey.model.script.Script, pathlib.Path]):
        start_time = datetime.datetime.now().time()
        # noinspection PyBroadException
        try:
            compiled_code = self._compile_script(script)
            exec(compiled_code, scope)
        except Exception:  # Catch everything raised by the User code. Those Exceptions must not crash the thread.
            traceback.print_exc()
            self._record_error(script, start_time)

    @staticmethod
    def _compile_script(script: typing.Union[autokey.model.script.Script, pathlib.Path]):
        script_code, script_name = ScriptRunner._get_script_source_code_and_name(script)
        compiled_code = compile(script_code, script_name, 'exec')
        return compiled_code

    @staticmethod
    def _get_script_source_code_and_name(script: typing.Union[autokey.model.script.Script, pathlib.Path]) -> typing.Tuple[str, str]:
        if isinstance(script, pathlib.Path):
            script_code = script.read_text()
            script_name = str(script)
        elif isinstance(script, autokey.model.script.Script):
            script_code = script.code
            if script.path is None:
                script_name = "<string>"
            else:
                script_name = str(script.path)
        else:
            raise TypeError(
                "Unknown script type passed in, expected one of [autokey.model.Script, pathlib.Path], got {}".format(
                    type(script)))
        return script_code, script_name

    @staticmethod
    def _set_triggered_abbreviation(scope: dict, buffer: str, trigger_character: str):
        """Provide the triggered abbreviation to the executed script, if any"""
        engine = scope["engine"]  # type: autokey.scripting.Engine
        if buffer:
            triggered_abbreviation = buffer[:-len(trigger_character)]

            logger.debug(
                "Triggered a Script by an abbreviation. Setting it for engine.get_triggered_abbreviation(). "
                "abbreviation='{}', trigger='{}'".format(triggered_abbreviation, trigger_character)
            )
            engine._set_triggered_abbreviation(triggered_abbreviation, trigger_character)

    def run_subscript(self, script: typing.Union[autokey.model.script.Script, pathlib.Path]):
        scope = self.scope.copy()
        if isinstance(script, autokey.model.script.Script):
            scope["store"] = script.store
            scope["__file__"] = str(script.path)
        else:
            scope["__file__"] = str(script.resolve())

        compiled_code = self._compile_script(script)
        exec(compiled_code, scope)
