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

import autokey.common


def generate_argument_parser() -> argparse.ArgumentParser:
    """Generates an ArgumentParser for AutoKey"""
    parser = argparse.ArgumentParser(description="Desktop automation ")
    parser.add_argument(
        "-l", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "-c", "--configure",
        action="store_true",
        dest="show_config_window",
        help="Show the configuration window on startup"
    )
    # %(prog)s substitution only works for installations. It shows "__main__.py", if run from the source tree.
    parser.add_argument(
        "-V", "--version",
        action="version",
        version="%(prog)s Version {}".format(autokey.common.VERSION)
    )
    return parser


def parse_args():
    """
    Parses the command line arguments
    :return: argparse Namespace object containing the parsed command line arguments
    """
    parser = generate_argument_parser()
    args = parser.parse_args()
    return args

