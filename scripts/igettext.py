#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 J. David Ibáñez <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import optparse
import os

# Import from itools
from itools.resources import get_resource
from itools.handlers import get_handler
from itools.handlers.Python import Python
from itools.gettext import PO
from itools.xhtml import XHTML


def run():
    """
    Return PO file.
    """
    # Parse the options
    parser = optparse.OptionParser()
    parser.add_option('-o', '--output',
                      dest='output',
                      help="The output will be sent to the given file,"
                           " instead of to the standard output.")
    parser.add_option('--pot',
                      action="store_const", const=0, dest='action',
                      help="Extracts the translatable messages from the"
                           " given list of files and outputs the POT file")
    parser.add_option('--po',
                      action="store_const", const=1, dest='action',
                      help="Updates the po file with the messages from the"
                           " POT file")
    parser.add_option('--xhtml',
                      action="store_const", const=2, dest='action',
                      help="Outputs a new XHTML file from the original source"
                           " and a PO file")
    options, args = parser.parse_args()

    # Action
    root_resource = get_resource('/')
    if options.action == 0:
        po = PO.PO()
        for source_file in args:
            # Load the source handler
            resource = get_resource(source_file)
            if source_file.endswith('.py'):
                handler = Python(resource)
            else:
                # XXX Suppose it is XHTML
                handler = XHTML.Document(resource)
            # Extract the messages
            for msgid, line_number in handler.get_messages():
                po.set_message(msgid, references={source_file: [line_number]})
            # XXX Should omit the header?
            output = po.to_str()
    elif options.action == 1:
        pot = args[0]
        po = args[1]
        if os.path.exists(po):
            # a .po file already exist, merge it with locale.pot
            output = os.popen('msgmerge -s %s %s' % (po, pot)).read()
        else:
            # po doesn't exist, just copy locale.pot
            output = open(pot).read()
    elif options.action == 2:
        resource = get_resource(args[0])
        xhtml = XHTML.Document(resource)
        po = get_handler(args[1])
        output = xhtml.translate(po)
    else:
        pass

    if options.output is None:
        print output
    else:
        open(options.output, 'w').write(output)



if __name__ == '__main__':
    run()
