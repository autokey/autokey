This directory contains the default user-scripts that ship with a new AutoKey installation.

- There is no `__init__.py`. This is not an AutoKey source-package. This is package-data that happens to be Python code.
- The files have the Python interface extension (`.pyi`) to emphasize that they're not part of the running AutoKey source.
- Because of missing imports, the files are not executable. This is intended. The missing imports belong to the AutoKey
  API and are injected at script runtime when executed by AutoKey.
- The script-files here are not automatically detected. To add a script, place the code here and define the metadata in
  `predefined_user_files.py` in the parent AutoKey package.
