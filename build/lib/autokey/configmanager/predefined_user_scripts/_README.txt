This directory contains the default user scripts that ship with a new AutoKey installation.

- There is no __init__.py. This is not a AutoKey source package. This is package data, that happens to be Python code.
- Files have the Python interface file ending (.pyi) to emphasise that files are not part of the running AutoKey source.
- The files are not executable, because of missing imports. This is intended. The missing imports belong to the AutoKey
  API and are injected at script runtime, when executed by AutoKey.
- Script files here are not automatically detected. To add a script, place the code here and define the meta-data in
  predefined_user_files.py in the parent AutoKey package.
