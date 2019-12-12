# This script is used to test script macros only.
print("running")

folder = engine.get_folder("Test folder")
phrase = engine.create_phrase(folder, "Phrase", "ABC", temporary=True)
