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

"""
This module contains the autostart handling code.
This setting is not handled in the autokey.json configuration file. Instead, automatically starting autokey at login
is handled by the presence of a autokey.desktop file in “$XDG_CONFIG_DIR/autostart/”.
"""
import typing
import logging
from pathlib import Path

from autokey import common

_logger = logging.getLogger("config-manager").getChild("autostart")  # type: logging.Logger

AutostartSettings = typing.NamedTuple("AutostartSettings", [
    ("desktop_file_name", typing.Optional[str]), ("switch_show_configure", bool)
])


def get_autostart() -> AutostartSettings:
    """Returns the autostart settings as read from the system."""
    autostart_file = Path(common.AUTOSTART_DIR) / "autokey.desktop"
    if not autostart_file.exists():
        return AutostartSettings(None, False)
    else:
        return _extract_data_from_desktop_file(autostart_file)


def _extract_data_from_desktop_file(desktop_file: Path) -> AutostartSettings:
    with open(str(desktop_file), "r") as file:
        for line in file.readlines():
            line = line.rstrip("\n")
            if line.startswith("Exec="):
                program_name = line.split("=")[1].split(" ")[0]
                return AutostartSettings(program_name + ".desktop", line.endswith("-c"))
    raise ValueError("Autostart autokey.desktop file does not contain any Exec line. File: {}".format(desktop_file))


def set_autostart_entry(autostart_data: AutostartSettings):
    """
    Activates or deactivates autostarting autokey during user login.
    Autostart is handled by placing a .desktop file into '$XDG_CONFIG_HOME/autostart', typically '~/.config/autostart'
    """
    _logger.info("Save autostart settings: {}".format(autostart_data))
    autostart_file = Path(common.AUTOSTART_DIR) / "autokey.desktop"
    if autostart_data.desktop_file_name is None:  # Choosing None as the GUI signals deleting the entry.
        delete_autostart_entry()
    else:
        autostart_file.parent.mkdir(exist_ok=True)  # make sure that the parent autostart directory exists.
        _create_autostart_entry(autostart_data, autostart_file)


def _create_autostart_entry(autostart_data: AutostartSettings, autostart_file: Path):
    """Create an autostart .desktop file in the autostart directory, if possible."""
    try:
        source_desktop_file = get_source_desktop_file(autostart_data.desktop_file_name)
    except FileNotFoundError:
        _logger.exception("Failed to find a usable .desktop file! Unable to find: {}".format(
            autostart_data.desktop_file_name))
    else:
        _logger.debug("Found source desktop file that will be placed into the autostart directory: {}".format(
            source_desktop_file))
        with open(str(source_desktop_file), "r") as opened_source_desktop_file:
            desktop_file_content = opened_source_desktop_file.read()
        desktop_file_content = "\n".join(_manage_autostart_desktop_file_launch_flags(
            desktop_file_content, autostart_data.switch_show_configure
        )) + "\n"
        with open(str(autostart_file), "w", encoding="UTF-8") as opened_autostart_file:
            opened_autostart_file.write(desktop_file_content)
        _logger.debug("Written desktop file: {}".format(autostart_file))


def delete_autostart_entry():
    """Remove a present autostart entry. If none is found, nothing happens."""
    autostart_file = Path(common.AUTOSTART_DIR) / "autokey.desktop"
    if autostart_file.exists():
        autostart_file.unlink()
        _logger.info("Deleted old autostart entry: {}".format(autostart_file))


def get_source_desktop_file(desktop_file_name: str) -> Path:
    """
    Try to get the source .desktop file with the given name.
    :raises FileNotFoundError: If no desktop file was found in the searched directories.
    """
    possible_paths = (
        # Copy from local installation. Also used if the user explicitely customized the launcher .desktop file.
        Path(common.XDG_DATA_HOME) / "applications",
        # Copy from system-wide installation
        Path("/", "usr", "share", "applications"),
        # Copy from git source tree. This will probably not work when used, because the application won’t be in the PATH
        Path(__file__).parent.parent.parent / "config"
    )
    for possible_path in possible_paths:
        desktop_file = possible_path / desktop_file_name
        if desktop_file.exists():
            return desktop_file
    raise FileNotFoundError("Desktop file for autokey could not be found. Searched paths: {}".format(possible_paths))


def _manage_autostart_desktop_file_launch_flags(desktop_file_content: str, show_configure: bool) -> typing.Iterable[str]:
    """Iterate over the desktop file contents. Yields all lines except for the "Exec=" line verbatim. Modifies
    the Exec line to include the user desired command line switches (currently only one implemented)."""
    for line in desktop_file_content.splitlines(keepends=False):
        if line.startswith("Exec="):
            exec_line = _modify_exec_line(line, show_configure)
            _logger.info("Used 'Exec' line in desktop file: {}".format(exec_line))
            yield exec_line
        else:
            yield line


def _modify_exec_line(line: str, show_configure: bool) -> str:
    if show_configure:
        if line.endswith(" -c"):
            return line
        else:
            return line + " -c"
    else:
        if line.endswith(" -c"):
            return line[:-3]
        else:
            return line
