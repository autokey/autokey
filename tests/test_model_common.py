"""
Regression tests for #1221: an item saved with the hotkey trigger disabled but a
hotkey still recorded must load with that trigger disabled.

AbstractHotkey.set_hotkey() force-adds TriggerMode.HOTKEY whenever a hotkey is
recorded. inject_json_data_base() used to assign item.modes before calling it, so
"modes": [] was overwritten on every load and the disabled item fired anyway.
"""
import json

import pytest
from hamcrest import *

from autokey.model.folder import Folder
from autokey.model.phrase import Phrase
from autokey.model.script import Script
from autokey.model.triggermode import TriggerMode


ITEM_FACTORIES = {
    "Phrase": lambda: Phrase("description", "phrase"),
    "Script": lambda: Script("description", "code"),
    "Folder": lambda: Folder("title"),
}


def reload(item, factory):
    """Round-trip item through JSON into a fresh instance, as loading from disk does."""
    data = json.loads(json.dumps(item.get_serializable()))
    fresh = factory()
    fresh.inject_json_data(data)
    return fresh


@pytest.mark.parametrize("factory", ITEM_FACTORIES.values(), ids=ITEM_FACTORIES.keys())
def test_disabled_hotkey_trigger_survives_reload(factory):
    item = factory()
    item.set_hotkey(["<hyper>"], "a")
    item.modes = []

    loaded = reload(item, factory)

    assert_that(loaded.modes, is_(empty()))
    # The recorded hotkey is kept, so re-enabling the trigger does not need it re-recorded.
    assert_that(loaded.hotKey, is_("a"))
    assert_that(loaded.modifiers, is_(["<hyper>"]))


@pytest.mark.parametrize("factory", ITEM_FACTORIES.values(), ids=ITEM_FACTORIES.keys())
def test_enabled_hotkey_trigger_survives_reload(factory):
    item = factory()
    item.set_hotkey(["<hyper>"], "a")
    item.modes = [TriggerMode.HOTKEY]

    loaded = reload(item, factory)

    assert_that(loaded.modes, is_([TriggerMode.HOTKEY]))


def test_phrase_file_with_hotkey_trigger_disabled_loads_disabled(tmp_path):
    """The reproducer from #1221, loaded from a file on disk as AutoKey does."""
    template = Phrase("testphrase", "phrase")
    data = template.get_serializable()
    data.update({"modes": [], "hotkey": {"modifiers": ["<hyper>"], "hotKey": "a"}})

    phrase_path = tmp_path / "testphrase.txt"
    phrase_path.write_text("phrase")
    phrase = Phrase("", "", path=str(phrase_path))
    with open(phrase.get_json_path(), "w") as json_file:
        json.dump(data, json_file)

    phrase.load_from_serialized()

    assert_that(phrase.modes, is_(empty()))
    assert_that(phrase.hotKey, is_("a"))
