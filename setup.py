#!/usr/bin/env python3
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

import sys
import re
from collections import namedtuple
import subprocess
from pathlib import Path, PurePath
import warnings
import shutil

try:
    from setuptools import setup
except ImportError:
    print("Autokey needs setuptools in order to build. Install it with your package"
          "manager (python-setuptools) or via pip (pip install setuptools)")
    sys.exit(1)
else:
    import setuptools.command.build_py

if sys.version_info < (3, 5, 0):
    print("Autokey requires Python 3.5 or later. You are using " + ".".join(map(str, sys.version_info[:3])))
    sys.exit(1)


AutoKeyData = namedtuple("AutoKeyData", ["version", "author", "author_email", "maintainer", "maintainer_email"])


def extract_autokey_data() -> AutoKeyData:
    source_file_name = "./lib/autokey/common.py"
    with open(source_file_name, "r") as data_source_file:
        source = data_source_file.read()
    if not source:
        print("Cannot read AutoKey source file containing required information. Unreadable: {}".format(
            source_file_name))
        sys.exit(1)

    def search_for(pattern: str) -> str:
        return re.search(
            r"""^{}\s*=\s*('(.*)'|"(.*)")""".format(pattern),  # Search for assignments: VAR = 'VALUE' or VAR = "VALUE"
            source,
            re.M
        ).group(1)[1:-1]  # Cut off outer quotation marks

    return AutoKeyData(
        version=search_for("VERSION"),
        author=search_for("AUTHOR"),
        author_email=search_for("AUTHOR_EMAIL"),
        maintainer=search_for("MAINTAINER"),
        maintainer_email=search_for("MAINTAINER_EMAIL")
    )


class BuildWithQtResources(setuptools.command.build_py.build_py):
    """Try to build the Qt resources file for autokey-qt."""
    def run(self):
        if not self.dry_run:
            resource_dir = (Path(__file__).parent / "lib" / "autokey" / "qtui" / "resources").resolve()
            resource_file = resource_dir / "resources.qrc"
            self._copy_icon_files_into_qt_resources_directory(resource_dir)
            compiled_qt_resources = self._compile_resource_file(resource_file)
            if compiled_qt_resources:
                target_directory = Path(self.build_lib) / "autokey" / "qtui"
                self.mkpath(str(target_directory))
                with open(str(target_directory / "compiled_resources.py"), "w") as compiled_qt_resources_file:
                    compiled_qt_resources_file.write(compiled_qt_resources)
            else:
                # If here, compilation failed for a known reason, so include the resource files directly.
                # Ok, always include this for now. setup.py seems to not like this
                # self.package_data["autokey.qtui"] += ["resources/icons/*", "resources/ui/*.ui"]
                pass
        super(BuildWithQtResources, self).run()

    @staticmethod
    def _compile_resource_file(resource_file: Path) -> str:
        command = ("pyrcc5", str(resource_file))
        try:
            compiled = subprocess.check_output(command, universal_newlines=True)  # type: str
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            warnings.warn("An exception occurred during resource compilation for autokey-qt: {}".format(e))
            return ""
        else:
            return compiled

    def _copy_icon_files_into_qt_resources_directory(self, resource_dir: Path):
        target_directory = resource_dir / "icons"
        self.mkpath(str(target_directory))
        icon_source_path = (Path(__file__).parent / "config").resolve()  # type: Path
        for icon_name in (
                "autokey.png",
                "autokey.svg",
                "autokey-status.svg",
                "autokey-status-dark.svg",
                "autokey-status-error.svg"):
            icon = icon_source_path / icon_name
            shutil.copy(str(icon), str(target_directory))


ak_data = extract_autokey_data()
this_directory = PurePath(__file__).parent
with open(this_directory / 'README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='autokey',
    version=ak_data.version,
    description='Keyboard and GUI automation on Linux (X11)',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author=ak_data.author,
    author_email=ak_data.author_email,
    maintainer=ak_data.maintainer,
    maintainer_email=ak_data.maintainer_email,
    url='https://github.com/autokey/autokey',
    cmdclass={'build_py': BuildWithQtResources},
    license='GPLv3',
    python_requires=">=3.5",
    # This requires autokey submodules (subdirectories) to contain their own `__init__.py` file (i.e.
    # they advertise themselves as modules).
    # find_namespace_packages might be a better alternative that doesn't
    # require this.
    # https://setuptools.readthedocs.io/en/latest/userguide/package_discovery.html#using-find-namespace-or-find-namespace-packages
    packages=setuptools.find_packages('lib'),
    package_dir={'': 'lib'},

    package_data={'autokey.qtui': ['data/*', 'resources/icons/*', 'resources/ui/*.ui'],
                  'autokey.gtkui': ['data/*']},
    data_files=[('share/icons/hicolor/scalable/apps',
                 ['config/autokey.svg',
                  'config/autokey-status.svg',
                  'config/autokey-status-dark.svg',
                  'config/autokey-status-error.svg']),
                ('share/icons/hicolor/96x96/apps',  # TODO: Remove later. https://github.com/autokey/autokey/issues/160
                 ['config/autokey.png']),
                ('share/icons/Humanity/scalable/apps',
                 ['config/Humanity/autokey-status.svg',
                  'config/Humanity/autokey-status-error.svg']),
                ('share/icons/ubuntu-mono-dark/apps/48',
                 ['config/ubuntu-mono-dark/autokey-status.svg',
                  'config/ubuntu-mono-dark/autokey-status-error.svg']),
                ('share/icons/ubuntu-mono-light/apps/48',
                 ['config/ubuntu-mono-light/autokey-status.svg',
                  'config/ubuntu-mono-light/autokey-status-error.svg']),
                ('share/applications',
                 ['config/autokey-qt.desktop',
                  'config/autokey-gtk.desktop']),
                ('share/man/man1/',
                 ['doc/man/autokey-qt.1',
                  'doc/man/autokey-gtk.1',
                  'doc/man/autokey-run.1'])
                ],
    entry_points={
        'console_scripts': [
            'autokey-gtk=autokey.gtkui.__main__:main',
            'autokey-qt=autokey.qtui.__main__:Application'
        ]
    },
    scripts=['autokey-run', 'autokey-shell'],
    # Minimal installation pre-requisite python packages.
    # Some are not included here because they should be installed
    # through the system package manager, not pip.
    install_requires=[
        'pyinotify',
        'python-xlib',
        'packaging',
    ],
    test_suite="pytest",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='automation hotkey expansion expander phrase',
)
