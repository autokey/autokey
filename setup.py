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
          "manager (python3-setuptools) or via pip (python3 -m pip install setuptools)")
    sys.exit(1)
else:
    import setuptools.command.build_py

if sys.version_info < (3, 10, 0):
    print("Autokey requires Python 3.10.0 or later. You are using " + ".".join(map(str, sys.version_info[:3])))
    sys.exit(1)


AutoKeyMetadata = namedtuple("AutoKeyMetadata", ["version", "author", "author_email", "maintainer", "maintainer_email"])


def extract_autokey_metadata() -> AutoKeyMetadata:
    source_file_name = "./lib/autokey/common.py"
    with open(source_file_name, "r") as metadata_source_file:
        source = metadata_source_file.read()
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

    return AutoKeyMetadata(
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
                # self.package_metadata["autokey.qtui"] += ["resources/icons/*", "resources/ui/*.ui"]
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


def ensure_gnome_shell_extension_zip() -> str:
    """
    Build the AutoKey GNOME Shell extension zip via its Makefile if it
    doesn't already exist, and return its path if available (empty string
    otherwise).

    Previously, `data_files` referenced this zip unconditionally, which
    meant a plain `pip install .` on a clean checkout failed outright with
    "can't copy ...: doesn't exist or not a regular file" unless a
    developer remembered to run `make -C autokey-gnome-extension` first --
    confirmed live, and confirmed to affect KDE-targeted installs
    (`pip install .[QT]`) exactly the same way, despite KDE never using
    this extension at all. Build it automatically here instead. If that
    fails for any reason (e.g. `zip` or `make` not installed), warn and
    proceed without it rather than aborting the whole install -- the
    extension is only needed for GNOME Wayland, and users on that path
    already get a popup from wayland_checks.py at runtime if it's missing.
    """
    # setup() requires data_files entries to be relative to the setup.py
    # directory, not absolute -- keep the relative form for the return
    # value, while still using an absolute path (robust to the caller's
    # cwd) to actually check for and build the file.
    relative_zip_path = "autokey-gnome-extension/autokey-gnome-extension@autokey.shell-extension.zip"
    extension_dir = Path(__file__).parent / "autokey-gnome-extension"
    absolute_zip_path = Path(__file__).parent / relative_zip_path
    if not absolute_zip_path.exists():
        try:
            subprocess.run(["make"], cwd=str(extension_dir), check=True)
        except Exception as e:
            warnings.warn(
                "Could not build the AutoKey GNOME Shell extension zip ({}). "
                "Continuing without it -- GNOME Wayland users will need to "
                "build and install it manually; see autokey-gnome-extension/README.md.".format(e)
            )
            return ""
    return relative_zip_path if absolute_zip_path.exists() else ""


ak_metadata = extract_autokey_metadata()
this_directory = PurePath(__file__).parent
with open(this_directory / 'README.rst', encoding='utf-8') as f:
    long_description = f.read()

gnome_shell_extension_zip = ensure_gnome_shell_extension_zip()

data_files_list = [
    ('share/icons/hicolor/scalable/apps',
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
      'doc/man/autokey-run.1']),
    ('share/autokey/uinput-udev-rule/',
     ['config/10-autokey.rules']),
]
if gnome_shell_extension_zip:
    # Only included if the zip could be built (or already existed) --
    # see ensure_gnome_shell_extension_zip(). Missing it should not block
    # installation, e.g. on KDE, which never uses it, or if `make`/`zip`
    # aren't available.
    data_files_list.append(
        ('share/autokey/gnome-shell-extension/', [gnome_shell_extension_zip])
    )

setup(
    name='autokey',
    version=ak_metadata.version,
    description='Keyboard and GUI automation on Linux',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author=ak_metadata.author,
    author_email=ak_metadata.author_email,
    maintainer=ak_metadata.maintainer,
    maintainer_email=ak_metadata.maintainer_email,
    url='https://github.com/autokey/autokey',
    cmdclass={'build_py': BuildWithQtResources},
    license='GPLv3',
    # setuptools_scm removes need for MANIFEST.in. Allows setuptools to get which files to
    # include in source distributions from git.
    # setup_requires=['setuptools_scm'],
    # Use setuptools_scm to get version number from git! (Gives tag, plus dev
    # commit details since most recent tag if not on tagged commit).
    # If using this, would have to also set common.VERSION from this so that
    # the autokey 'about' menu shows the correct version.
    # use_scm_version=True,
    python_requires=">=3.10",
    # This requires autokey submodules (subdirectories) to contain their own `__init__.py` file (i.e.
    # they advertise themselves as modules).
    # find_namespace_packages might be a better alternative that doesn't
    # require this.
    # https://setuptools.readthedocs.io/en/latest/userguide/package_discovery.html#using-find-namespace-or-find-namespace-packages
    packages=setuptools.find_packages('lib'),
    package_dir={'': 'lib'},
    include_package_data=True,
    package_data={'autokey': ["configmanager/predefined_user_scripts/*"],
        'autokey.qtui': ['data/*',
            'resources/icons/*',
            'resources/ui/*.ui'],
        'autokey.gtkui': ['data/*'],
        },
    data_files=data_files_list,
    entry_points={
        'console_scripts': [
            'autokey-headless=autokey.headless_app:main',
        ]
    },
    scripts=['autokey-gtk', 'autokey-qt', 'autokey-run', 'autokey-shell'],
    # Minimal installation pre-requisite python packages.
    # Some are not included here because they should be installed
    # through the system package manager, not pip.
    install_requires=[
        'pyasyncore',
        'pyinotify',
        'python-xlib',
        'packaging',
        'python-magic',
        'pyasyncore; python_version>="3.12"',
        # Required by uinput_interface.py, which is used on Wayland
        # (both GNOME and KDE) regardless of front end. Neither is
        # declared here currently, so a fresh `pip install .` on a
        # system without these already present as system packages
        # fails at runtime with ModuleNotFoundError as soon as a
        # Wayland session tries to start the input interface, even
        # though the install itself appears to succeed. Confirmed live
        # on a fresh Ubuntu 22.04.5 VM.
        'evdev',
        'pyudev',
        # Required by kde_interface.py specifically (imported directly,
        # unconditionally, as soon as autokey.iomediator.iomediator is
        # loaded on a KDE desktop). Same gap as evdev/pyudev above:
        # declared in the CI-only pip-requirements.txt but missing here,
        # so a fresh KDE Wayland install fails with
        # "ModuleNotFoundError: No module named 'pydbus'" at startup.
        # Confirmed live on a fresh Kubuntu 26.04.1 VM (Plasma 6.6.6).
        'pydbus',
    ],
    extras_require={
            "QT": [
                "PyQt5",
                "QScintilla"
                ],
            "GTK": [
                "PyGObject"
                ]
            },
    test_suite="pytest",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.10',
    ],
    keywords='automation hotkey expansion expander phrase macros keyboard auto key autokey ak shortcuts bind autohotkey mouse customization',
)
