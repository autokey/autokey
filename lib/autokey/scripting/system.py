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

"""Provides access to run system commands through C{subprocess} and basic file creation"""

import subprocess


class System:
    """
    Simplified access to some system commands.
    """
    @staticmethod
    def exec_command(command, getOutput=True):
        """
        Execute a shell command

        Usage: C{system.exec_command(command, getOutput=True)}

        Set getOutput to False if the command does not exit and return immediately. Otherwise
        AutoKey will not respond to any hotkeys/abbreviations etc until the process started
        by the command exits.

        :param command: command to be executed (including any arguments) - e.g. "ls -l"
        :param getOutput: whether to capture the (stdout) output of the command
        :raise subprocess.CalledProcessError: if the command returns a non-zero exit code
        """
        if getOutput:
            with subprocess.Popen(
                    command,
                    shell=True,
                    bufsize=-1,
                    stdout=subprocess.PIPE,
                    universal_newlines=True) as p:
                output = p.communicate()[0]
                # Most shell output has a new line at the end, which we don't want.
                output = output.rstrip("\n")
                if p.returncode:
                    raise subprocess.CalledProcessError(p.returncode, output)
                return output
        else:
            subprocess.Popen(command, shell=True, bufsize=-1)

    @staticmethod
    def create_file(file_name, contents=""):
        """
        Create a file with contents

        Usage: C{system.create_file(fileName, contents="")}

        :param file_name: full path to the file to be created
        :param contents: contents to insert into the file
        """
        with open(file_name, "w") as written_file:
            written_file.write(contents)
