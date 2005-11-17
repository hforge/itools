#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

# Import from the Standard Library
import os
import sys

# Import from ZODB
from optparse import OptionParser
from ZODB.FileStorage import FileStorage

# Import from itools
import itools
from itools.resources import base, get_resource, zodb
from itools.web.server import Server
from itools.cms.Root import Root



if __name__ == '__main__':
    revision = itools.__arch_revision__
    version = revision.split('--')[2]
    parser = OptionParser(usage='usage: %prog [options] directory',
                          version='itools %s [%s]' % (version, revision))
    parser.add_option('-p', '--port', type='int', help='listen to port number')
    parser.add_option('-i', '--import', dest='import_resource',
                      help='import instance from directory')

    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    # If the user wants to import, check wether there is really an ikaaro
    # instance in the import directory
    import_resource = options.import_resource
    if import_resource is not None:
        import_resource = get_resource(import_resource)
        if not isinstance(import_resource, base.Folder):
            parser.error('can not import instance (not a folder)')
        if not import_resource.has_resource('.metadata'):
            parser.error('can not import instance (bad folder)')

    # Create the instance
    path = args[0]
    try:
        os.mkdir(path)
    except OSError:
        pass

    # Load the root resource
    storage = FileStorage('%s/database.fs' % path)
    database = zodb.Database(storage)
    root_resource = database.get_resource('/')

    # Check wether the user wants to import an instance to a non-empty database
    if import_resource and root_resource.get_resource_names():
        parser.error('can not import instance (database not empty)')

    # Create an instance if there is not
    if not root_resource.has_resource('.metadata'):
        if import_resource:
            source = import_resource
        else:
            source = Root(username='a', password='a').resource

        for name in source.get_resource_names():
            resource = source.get_resource(name)
            root_resource.set_resource(name, resource)
        root_resource.get_transaction().commit()

    # Load the root handler
    root = Root(root_resource)
    root.name = 'root'

    # Start the server
    server = Server(root, port=options.port, access_log='%s/access_log' % path,
                    error_log='%s/error_log' % path, pid_file='%s/pid' % path)
    server.start()
