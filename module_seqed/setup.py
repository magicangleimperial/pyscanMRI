import sys
from cx_Freeze import setup, Executable



base = None
if sys.platform == 'win64':
    base = "Win64GUI"

build_exe_options = {}

setup( name = "Sequence Editor",
       version = "0.8.4",
       description = "The sequence editor application.",
       options = {"build_exe": build_exe_options},
       executables = [Executable("main.py", base=base)]
    )