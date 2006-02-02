#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Luis A. Belmar Letelier <luis@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# import from Python
from optparse import OptionParser
from pprint import pprint
import glob, tempfile, sys, os

# import from itools
from itools.handlers import get_handler
from itools.handlers.python import Python
from itools.handlers.dot import Dot


if __name__ == "__main__":
    usage = ("      %prog [file.py]*\n"
             "This produce in a 'out.dot' file")
    parser = OptionParser(usage=usage)
    options, args = parser.parse_args()
    if not args:
        args = glob.glob('*.py')
    if not len(args):
        print os.system('itaapyTools_classDiagram.py --help')
        sys.exit()

    here = get_handler('.')
    # we need the name of the package
    here.name = os.getcwd().split('/')[-1]

    python_handlers = []
    for name in args:
        h = here.get_handler(name)
        h.name = name.split('.py')[0]
        h.package_name = h.get_package_name()
        python_handlers.append(h)

    dot = Dot()
    dot.class_diagram_from_python(python_handlers)
    dot_data = dot.to_str()

    open('out.dot', 'w').write(dot_data)
    print 'dot -Tps out.dot > out.ps; gv out.ps'


