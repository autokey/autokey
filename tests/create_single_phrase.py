# flake8: noqa: F821
# This script is used to test script macros only.
print("running")
args = engine.get_macro_arguments()
folder = engine.get_folder("Test folder")
phrase = engine.create_phrase(folder, args[0], args[1], temporary=True)
