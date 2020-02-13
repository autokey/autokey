# This script is used to test script macros only.
print("running")
args = engine.get_macro_arguments()
folder = engine.get_folder("Test folder")
phrase = engine.create_phrase(folder, arg[0], arg[1], temporary=True)
