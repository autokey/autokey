# Copyright (C) 2018 Thomas Hess
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

"""
Contains common functions for both Qt and Gtk versions
"""

from typing import NamedTuple, Union, List


class ColourData(NamedTuple("ColourData", (("r", int), ("g", int), ("b", int)))):
    """Colour data type for colour chooser dialogs."""
    @property
    def hex_code(self) -> str:
        """Returns rgb in hex format"""
        return "{0:02x}{1:02x}{2:02x}".format(self.r, self.g, self.b)

    @property
    def html_code(self) -> str:
        """Converts the ColourData into a HTML-style colour, equivalent to the KDialog output."""
        return "#" + self.hex_code

    @property
    def zenity_tuple_str(self) -> str:
        """Converts the ColourData into a tuple-like string, equivalent to the Zenity output. ("rgb(R, G, B)")"""
        return "rgb({})".format(",".join(map(str,self)))

    @staticmethod
    def from_html(html_style_colour_str: str):
        """
        Parser for KDialog output, which outputs a HTML style hex code like #55aa00

        @param html_style_colour_str: HTML style hex string encoded colour. (#rrggbb)
        @return: ColourData instance
        @rtype: ColourData
        """
        html_style_colour_str = html_style_colour_str.lstrip("#")
        components = list(map("".join, zip(*[iter(html_style_colour_str)]*2)))
        return ColourData(*(int(colour, 16) for colour in components))

    @staticmethod
    def from_zenity_tuple_str(zenity_tuple_str: str):
        """
        Parser for Zenity output, which outputs a named tuple-like string: "rgb(R, G, B)", where R, G, B are base10
        integers.
        
        @param zenity_tuple_str: tuple-like string: "rgb(r, g, b), where r, g, b are base10 integers.
        @return: ColourData instance
        @rtype: ColourData
        """
        components = zenity_tuple_str.strip("rgb()").split(",")
        return ColourData(*map(int, components))


class DialogData(NamedTuple("DialogData", (("return_code", int), ("data", Union[ColourData, str, List[str], None])))):
    """Dialog data type for return values from input dialogs"""
    @property
    def successful(self) -> bool:
        """
        Returns True, if the dialog execution was successful, i.e. KDialog or Zenity exited with a zero return value.
        This includes:
        - Command line parameters are correct
        - Execution is otherwise successful (Can open X Display, load shared libraries, etc.)
        - The user clicked on OK or otherwise 'accepted' the dialog.
        """
        return self.return_code == 0


