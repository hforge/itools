#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
import sys
from xml.parsers.expat import ParserCreate



def start_element(name, attrs):
    pass

def end_element(name):
    pass

def char_data(data):
    pass


if __name__ == '__main__':
    # Read input parameters
    filename = sys.argv[1]
    nb_repeat = int(sys.argv[2])

    # Open the test file
    test_file = open(filename)

    # Loop
    while nb_repeat > 0:
        nb_repeat -= 1
        # Raise MemoryError after calling seek(0)
        # if we don't create a new parser
        p = ParserCreate()
        p.StartElementHandler = start_element
        p.EndElementHandler = end_element
        try:
            p.ParseFile(test_file)
        except:
            # Error
            test_file.close()
            exit(1)
        test_file.seek(0)

    # Ok
    test_file.close()
