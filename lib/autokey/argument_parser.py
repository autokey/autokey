# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import argparse
from typing import NamedTuple

import autokey.common

__all__ = [
    "Namespace",
    "parse_args"
]

Namespace = NamedTuple("Namespace", [
    # Mock Namespace that mimics the object returned by parse_args() and should have the same signature.
    # Used to provide better static type checking inside the IDE. Can also be used for unit testing.
    # TODO: Convert to a class when the minimum Python version is risen to >= 3.6.
    ("configure", bool),
    ("cutelog", bool),
    ("mouse", bool),
    ("verbose", bool),
    ("version", bool),
])


def _generate_argument_parser() -> argparse.ArgumentParser:
    """Generates an ArgumentParser for AutoKey"""
    parser = argparse.ArgumentParser(description="desktop automation ")
    parser.add_argument(
        "-c", "--configure",
        action="store_true",
        dest="show_config_window",
        help="open the AutoKey main window"
    )
    parser.add_argument(
        "-C", "--cutelog",
        action="store_true",
        help="connect to a local default cutelog instance to display the full program log"
    )
    parser.add_argument(
        "-g", "--grabkey",
        action="store_true",
        dest="grabkey_logging",
        help="enable verbose logging including X11 \"grabbing hotkey\" events"
    )
    parser.add_argument(
        "-m", "--mouse",
        action="store_true",
        dest="mouse_logging",
        help="enable verbose logging including mouse button events"
    )
    parser.add_argument(
        "-v", "--verbose", "-l",
        action="store_true",
        help="enable verbose logging (-l is deprecated)"
    )
    # %(prog)s substitution only works for installations. It shows "__main__.py", if run from the source tree.
    parser.add_argument(
        "-V", "--version",
        action="version",
        help="print the current AutoKey version to standard output",
        version="%(prog)s Version {}".format(autokey.common.VERSION)
    )
    return parser


def parse_args() -> Namespace:
    """
    Parses the command line arguments.
    :return: argparse Namespace object containing the parsed command line arguments
    """
    parser = _generate_argument_parser()
    args = parser.parse_args()
    #  Make sure verbose logging is also turned on when either --mouse or --grabkey options are used
    if args.mouse_logging and not args.verbose:
        args.verbose = True
    if args.grabkey_logging and not args.verbose:
        args.verbose = True
    # Share parsed command line arguments with other modules
    autokey.common.ARGS = args
    return args
