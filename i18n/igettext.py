#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003 J. David Ibáñez <jdavid@itaapy.com>
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


# Import from Python
import optparse
import os
import tempfile

# Import from itools
from itools.resources import get_resource
from itools.handlers import get_handler, PO
from itools.xml import XHTML


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
    root = get_handler('/')
    if options.action == 0:
        # Create one auxiliar PO file for each input file
        tmp_files = []
        for source_file in args:
            # Create the temp file and add it to the list
            tmp_file = tempfile.mktemp('.po')

            # Write the file's content
            if source_file.endswith('.py'):
                os.system('xgettext --omit-header --keyword=ugettext --keyword=N_ --output=%s %s' % (tmp_file, source_file))
            else:
                # XXX Suppose it is HTML
                po = PO.PO()
                resource = get_resource(source_file)
                xhtml = XHTML.Document(resource)
                for msgid in xhtml.get_messages():
                    po.set_message(msgid, references={source_file: [0]})
                root.set_handler(tmp_file, po)

            if os.path.exists(tmp_file):
                tmp_files.append(tmp_file)

        # Merge all the PO files
        command = 'msgcat -s %s' % ' '.join(tmp_files)
        output = os.popen(command).read()

        # Remove all the used files
        for file in tmp_files:
            os.remove(file)
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

    # Encode to UTF8 if needed
    if isinstance(output, unicode):
        output = output.encode('utf8')

    if options.output is None:
        print output
    else:
        open(options.output, 'w').write(output)



if __name__ == '__main__':
    run()
