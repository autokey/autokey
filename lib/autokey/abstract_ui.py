#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2021 BlueDrink9
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
from abc import ABC, ABCMeta, abstractmethod

class AutokeyUIInterface(ABC):
    __metaclass__ = ABCMeta

    @abstractmethod
    def show_error_dialog(self, message: str, details: str=None):
        pass


    @abstractmethod
    def shutdown(self):
        pass

    @abstractmethod
    def show_popup_menu(self):
        pass
