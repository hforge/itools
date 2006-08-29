#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Luis A. Belmar Letelier <luis@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# import from Python
from optparse import OptionParser
import glob, sys, os
import subprocess

# import from itools
from itools.handlers import get_handler
from itools.handlers.dot import class_diagram_from_python


if __name__ == "__main__":
    usage = ("      %prog [file.py]*\n"
             "This produce in a 'out.dot' file")
    parser = OptionParser(usage=usage)
    options, args = parser.parse_args()
    if not args:
        args = glob.glob('*.py')
    if not len(args):
        subprocess.call(['igraph.py', '--help'], stdout=sys.stdout)
        sys.exit()

    base_path = os.getcwd()
    here = get_handler('.')
    handlers = [ here.get_handler(x) for x in args ]

    dot_data = class_diagram_from_python(handlers, base_path)
    open('out.dot', 'w').write(dot_data)

    print 'dot -Tps out.dot > out.ps; gv out.ps'

