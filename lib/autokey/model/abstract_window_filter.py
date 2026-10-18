# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2019-2020 Thomas Hess <thomas.hess@udo.edu>
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

import re
import typing


class AbstractWindowFilter:

    # Class-level default. AbstractHotkey.__init__() does not call
    # AbstractWindowFilter.__init__(), so subclasses such as GlobalHotkey set the
    # filter attributes by hand. The class attribute keeps this one safe for any
    # subclass that does not, and for objects observed mid-deserialization.
    isInverted = False

    def __init__(self):
        self.windowInfoRegex = None
        self.isRecursive = False
        self.isInverted = False

    def get_serializable(self):
        if self.windowInfoRegex is not None:
            return {
                "regex": self.windowInfoRegex.pattern,
                "isRecursive": self.isRecursive,
                "isInverted": self.isInverted,
            }
        else:
            # Hardcoded rather than read from self: both UIs skip the filter
            # dialog's save() when the filter is disabled and call
            # set_window_titles(None) instead, which leaves a stale flag behind.
            return {"regex": None, "isRecursive": False, "isInverted": False}

    def load_from_serialized(self, data):
        try:
            if isinstance(data, dict): # check needed for data from versions < 0.80.4
                self.set_window_titles(data["regex"])
                self.isRecursive = data["isRecursive"]
                # .get(): config files written before this option existed have no
                # such key, and a KeyError here is swallowed by the broad handler
                # in model/common.py, silently half-loading the item.
                self.isInverted = bool(data.get("isInverted", False))
            else:
                self.set_window_titles(data)
        except re.error as e:
            raise e

    def copy_window_filter(self, window_filter):
        self.windowInfoRegex = window_filter.windowInfoRegex
        self.isRecursive = window_filter.isRecursive
        self.isInverted = window_filter.isInverted

    def set_window_titles(self, regex):
        if regex is not None:
            try:
                self.windowInfoRegex = re.compile(regex, re.UNICODE)
            except re.error as e:
                raise e
        else:
            self.windowInfoRegex = regex

    def set_filter_recursive(self, recurse):
        self.isRecursive = recurse

    def set_filter_invert(self, invert):
        self.isInverted = bool(invert)

    def has_filter(self) -> bool:
        return self.windowInfoRegex is not None

    def inherits_filter(self) -> bool:
        if self.parent is not None:
            return self.parent.get_applicable_regex(True) is not None

        return False

    def get_child_filter(self):
        if self.isRecursive and self.windowInfoRegex is not None:
            return self.get_filter_regex()
        elif self.parent is not None:
            return self.parent.get_child_filter()
        else:
            return ""

    def get_filter_regex(self):
        """
        Used by the GUI to obtain human-readable version of the filter
        """
        if self.windowInfoRegex is not None:
            if self.isRecursive:
                return self.windowInfoRegex.pattern
            else:
                return self.windowInfoRegex.pattern
        elif self.parent is not None:
            return self.parent.get_child_filter()
        else:
            return ""

    def filter_matches(self, otherFilter, otherInverted=False):
        """
        Whether this item's filter is indistinguishable from the one described by
        otherFilter/otherInverted.

        Used to decide whether two items may share a trigger: AutoKey allows that
        when their window filters differ. The same pattern with opposite polarity
        describes two disjoint sets of windows -- "only in X" and "everywhere but
        X" -- so those must compare as different, or the second item cannot be
        saved.
        """
        # XXX Should this be and?
        if otherFilter is None or self.get_applicable_regex() is None:
            return True

        if self.get_applicable_filter_inverted() != bool(otherInverted):
            return False

        return otherFilter == self.get_applicable_regex().pattern

    def same_filter_as_item(self, otherItem):
        if not isinstance(otherItem, AbstractWindowFilter):
            return False
        return self.filter_matches(otherItem.get_applicable_regex)

    def get_applicable_regex(self, forChild=False):
        if self.windowInfoRegex is not None:
            if (forChild and self.isRecursive) or not forChild:
                return self.windowInfoRegex
        elif self.parent is not None:
            return self.parent.get_applicable_regex(True)

        return None

    def get_applicable_filter_inverted(self, forChild=False) -> bool:
        """
        Return the invert flag belonging to whichever item supplies the applicable
        regex. Deliberately mirrors get_applicable_regex() line for line, so that an
        inherited filter carries the *parent's* invert flag rather than the child's.

        Only a genuine True inverts. The supported paths all store a real bool, so
        this is a fail-safe for anything else that reaches here -- a test double, a
        stub parent, a partially constructed item -- which degrades to the previous
        include-only behaviour rather than silently inverting every item that has no
        filter of its own.
        """
        if self.windowInfoRegex is not None:
            if (forChild and self.isRecursive) or not forChild:
                return self.isInverted is True
        elif self.parent is not None:
            return self.parent.get_applicable_filter_inverted(True) is True

        return False

    def _should_trigger_window_title(self, window_info):
        r = self.get_applicable_regex()  # type: typing.Pattern
        if r is None:
            return True

        matched = bool(r.match(window_info.wm_title)) or bool(r.match(window_info.wm_class))
        if self.get_applicable_filter_inverted():
            # not (title or class): the window is excluded if EITHER property
            # matches. This is what a negative lookahead in the regex cannot
            # express, because the regex is applied to each property separately.
            return not matched
        return matched

    def _should_grab_on_window(self, window_info) -> bool:
        """
        Whether an X11 key grab belongs on this specific window.

        Distinct from _should_trigger_window_title(): the callers in interface.py
        obtain WindowInfo with traverse=False, so window-manager frames and other
        intermediate windows report an empty title and class. For an include filter
        an empty WindowInfo simply fails to match and the tree walk descends. For an
        inverted filter it would "not match" and therefore claim the entire subtree,
        including the application the user asked to exclude.
        """
        if not window_info.wm_title and not window_info.wm_class:
            return False
        return self._should_trigger_window_title(window_info)
