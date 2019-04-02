#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2011
# Free Software Foundation, Inc.
#
# This file is part of the gtk-fortran gtk+ Fortran Interface library.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# Under Section 7 of GPL version 3, you are granted additional
# permissions described in the GCC Runtime Library Exception, version
# 3.1, as published by the Free Software Foundation.
#
# You should have received a copy of the GNU General Public License along with
# this program; see the files COPYING3 and COPYING.RUNTIME respectively.
# If not, see <http://www.gnu.org/licenses/>.
#
# Contributed by Vincent Magnin, 04.04.2011
# Last modification: vmagnin 2019-04-02

import os
import csv
import time
import re        # Regular expression library
import argparse  # To parse command line


def multiline(line, max_length):
    """Split a long line in a multiline, following Fortran syntax, and trying to
       cut it with elegance.
    """
    max_offset = max_length-1
    result = ""

    while len(line) > max_offset:
        # Remember that character max_length is excluded in such slice:
        string = line[0:max_length]

        cut = max_offset
        # We try to cut before a space, if reasonably possible:
        if string[cut] != " ":
            # Search the last space after the middle of the string:
            last_space = string.rfind(" ", max_length//2)
            if last_space != -1:
                cut = last_space

        result += line[0:cut] + "&\n"
        line = "&"+ line[cut:]

    # Add last line without trailing spaces:
    result += line.rstrip()

    return result


#*************************************
# Main program
#*************************************

# Definition of command line options:
PARSARG = argparse.ArgumentParser(description="This program scan all the Fortran files in the given directory and subdirectories to generate a usemodules.txt file with USE statements you can paste in your gtk-fortran programs. It also print warnings if you use deprecated GTK functions, and finally displays all the GTK functions used in a directory.",
                                  epilog="GPLv3 license, https://github.com/vmagnin/gtk-fortran")
PARSARG.add_argument("dir_path", action="store", type=str, nargs=1,
                     help="Path of the directory to scan")
ARGS = PARSARG.parse_args()

path = ARGS.dir_path[0]    # for example "../examples/"
if not path.endswith(os.sep):
    path += os.sep    # add directory separator on some operating systems

output_file = open("usemodules.txt", "w")
HEADER = """File generated by usemodules.py (gtk-fortran project)
Note that you should adapt these USE statements to each scope unit.
The script just identifies all the functions used in a given file.
You will generally need to add:
  & g_signal_connect, gtk_init, FALSE, TRUE, CNULL, GDK_COLORSPACE_RGB, GDK_COLORSPACE_RGB,&
  & GTK_WINDOW_TOPLEVEL, NULL
You should also add enums identifiers and parameters.
\n
"""
output_file.write(HEADER)

# Initialization:
used_functions = []
total = 0
nb_deprecated = 0

# Scan each directory:
for directory in os.walk(path):
    # Scan each file in that directory:
    for f_name in directory[2]:
        # Is it a Fortran file ? (.f or .f?? extension)
        if re.search(r"\.f(?:$|[\d]{2}$)", f_name) is None:
            continue    # to next file
        # The gtk-fortran *-auto.f90 files are not treated:
        if "-auto" in f_name:
            continue    # to next file

        print(f_name)

        only_dict = {}
        used_modules = []

        # Read the whole file in a string:
        whole_file = open(directory[0] + os.sep + f_name, 'r').read()

        # Load the GTK functions index generated by cfwrapper.py:
        reader = csv.reader(open("gtk-fortran-index.csv", "r"), delimiter=";")

        # Scan all functions in that index file:
        for row in reader:
            module_name     = row[0]
            function_name   = row[1]
            function_status = row[2]

            pattern = function_name + r"[^a-zA-Z0-9_]"

            if re.search(pattern, whole_file) is not None:
                # Is this module found for the first time ?
                if module_name not in used_modules:
                    used_modules.append(module_name)
                    only_dict[module_name] = "use "+module_name+", only: "

                only_dict[module_name] += function_name + ", "

                # Is this GTK function found for the first time ?
                if function_name not in used_functions:
                    used_functions.append(function_name)
                    total += 1

                # Is this function deprecated ?
                if "DEPRECATED" in function_status:
                    print(">>> " + function_status + ": " + function_name)
                    nb_deprecated += 1

        # Writes the USE statements needed for this Fortran file:
        output_file.write(f_name+"\n"+"============\n")
        for key in list(only_dict.keys()):
            output_file.write(multiline(only_dict[key].rstrip(", "), 80)+"\n")
        output_file.write("\n\n")


output_file.close()

print("*********************************************")
print(">>> ", nb_deprecated, " DEPRECATED calls")
print("*********************************************")

# To update the "Tested functions" wiki page:
used_functions.sort()
print()
print(total, "used functions, updated on", time.asctime(time.localtime()), "\n")
print(used_functions)
