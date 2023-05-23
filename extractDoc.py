# -*- coding: utf-8 -*-

# Copyright (C) 2023 Sam Sebastian

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import ast
import csv
import pathlib

def get_api(filepath, module_name=None, csv=False):
    """
    Reads in a python file, parses with `ast`, builds a list of the functions available in the file.

    Ignores functions that start with a "_" these are typically considered internal and should only be used by those who know of them.

    
    :param filepath: Filepath to load python script from
    :param module_name: Over write the module name, used for highlevel, qt/gtk specific things
    :param csv: changes output to csv, for use with Gtk autocompletion file
    """
    api = []
    with open(filepath, 'r') as f:
        module_ast = ast.parse(f.read())

    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef): # mostly highlevel where there is not a class
            #print(node.name)

            args = [arg.arg for arg in node.args.args if arg.arg != "self"]
            

            # grab only the first line of the doc string
            if node.name[0] == "_": #skip internal methods
                continue

            comment = ast.get_docstring(node)
            if comment:
                comment = comment.split('\n')[0]

            line = ""
            module_name_output = module_name
            if module_name is None:
                module_name_output = pathlib.Path(filepath).stem # for engine functions outside of the class, returns "engine"
                

            if csv:
                line = [f"{module_name_output}.{node.name}({', '.join(args)})", comment]
            else:
                line = f"{module_name_output}.{node.name}({', '.join(args)}) {comment}"

            api.append(line)

        elif isinstance(node, ast.ClassDef): # most other api will be running through here
            for method in node.body:
                #print(method, dir(method))
                if isinstance(method, ast.FunctionDef) and method.name != "__init__":

                    args = [arg.arg for arg in method.args.args if arg.arg != "self"]

                    if method.name[0] == "_": # if method starts with _, consider it internal
                        continue

                    # grab only the first line of the doc string
                    comment = ast.get_docstring(method)
                    if comment:
                        comment = comment.split('\n')[0]

                    line = ""
                    module_name_output = module_name
                    if module_name is None:
                        module_name_output = node.name.lower()


                    if csv:
                        line = [f"{module_name_output}.{method.name}({', '.join(args)})", comment]
                    else:
                        line = f"{module_name_output}.{method.name}({', '.join(args)}) {comment}"

                    api.append(line)

    return api

def get_macro(filepath):
    """
    Reads in the lib/autokey/macro.py and parses out classes that extend "AbstractMacro".
    Reads the ID, TITLE and ARGS values and returns a list of the macros found

    :param filepath: Filepath to read in and parse, currently only lib/autokey/macro.py would work here.
    """
    macro = []

    with open(filepath, 'r') as f:
        module_ast = ast.parse(f.read())

    for class_node in module_ast.body:
        var_name = ""
        name=""
        description=""
        args = []
        if isinstance(class_node, ast.ClassDef):
            if class_node.bases and class_node.bases[0].id=="AbstractMacro":
                for node in class_node.body:
                    if isinstance(node, ast.Assign):
                        var_name = node.targets[0].id
                        
                        if isinstance(node.value, ast.Constant):
                            name = node.value.s

                        # because TITLE is wrapped in translate it's considered a call, have to handle that differently
                        if isinstance(node.value, ast.Call): 
                            description = node.value.args[0].value

                        if isinstance(node.value, ast.List):
                            
                            for arg in node.value.elts:
                                if isinstance(arg, ast.Tuple):
                                    for item in arg.elts:
                                        if isinstance(item, ast.Call):
                                            arg_description = item.args[0].value
                                        elif isinstance(item, ast.Constant):
                                            arg_name = item.value

                                    #print(item, arg_name, arg_description)
                                    args.append([arg_name, arg_description])

                        
                        #print(var_name, name, description, node.value)
                        arguments = ""
                        if args:
                            arguments = " "
                            for arg in args:
                                arguments += f'{arg[0]}="{arg[1]}" '
                        
                        line = [f"<{name}{arguments.rstrip()}>", description]
                
                #print(line)
                macro.append(line)

    return macro



api = []
api += get_api("./lib/autokey/scripting/keyboard.py")
api += get_api("./lib/autokey/scripting/mouse.py")
api += get_api("./lib/autokey/scripting/window.py")
api += get_api("./lib/autokey/scripting/system.py")
api += get_api("./lib/autokey/scripting/engine.py")
api += get_api("./lib/autokey/scripting/highlevel.py", "highlevel")
api += get_api("./lib/autokey/scripting/abstract_clipboard.py", "clipboard")
api += get_api("./lib/autokey/scripting/dialog_qt.py", "dialog")
api += get_api("./lib/autokey/model/store.py")
# common.py holds classes that are returned by other things, doesn't need to be autocompleted.
#api += get_api("./lib/autokey/scripting/common.py")

filename = "./lib/autokey/qtui/data/api.txt"
print("Qt Autocomplete:", filename)
print("\n".join(api))

with open(filename, 'w') as f:
    f.write("\n".join(api))



# build out api.csv for GtkAutocomplete, writes as csv file
csv_api = []
csv_api += get_api("./lib/autokey/scripting/keyboard.py", csv=True)
csv_api += get_api("./lib/autokey/scripting/mouse.py", csv=True)
csv_api += get_api("./lib/autokey/scripting/window.py", csv=True)
csv_api += get_api("./lib/autokey/scripting/system.py", csv=True)
csv_api += get_api("./lib/autokey/scripting/engine.py", csv=True)
csv_api += get_api("./lib/autokey/scripting/highlevel.py", "highlevel", csv=True)
csv_api += get_api("./lib/autokey/scripting/abstract_clipboard.py", "clipboard", csv=True)
csv_api += get_api("./lib/autokey/scripting/dialog_gtk.py", "dialog", csv=True)
csv_api += get_api("./lib/autokey/model/store.py", csv=True)
#csv_api += get_api("./lib/autokey/scripting/common.py", csv=True)

filename = "./lib/autokey/gtkui/data/api.csv"
print("#"*80)
print("GTK Autocomplete:", filename)
[print(",".join(str(x) for x in line)) for line in csv_api]

with open(filename, 'w') as f:
    writer = csv.writer(f)

    for line in csv_api:
        writer.writerow(line)



macros = []
macros+=get_macro("./lib/autokey/macro.py")

filename = "./lib/autokey/gtkui/data/macros.csv"
print("#"*80)
print("GTK Macros:", filename)
[print(",".join(str(x) for x in line)) for line in macros]

with open(filename, 'w') as f:
    writer = csv.writer(f)

    for line in macros:
        writer.writerow(line)