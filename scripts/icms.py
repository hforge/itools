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
from ConfigParser import RawConfigParser
import os
import sys

# Import from ZODB
from optparse import OptionParser
from ZODB.FileStorage import FileStorage

# Import from itools
import itools
from itools.resources import base, get_resource, zodb
from itools.web.server import Server
from itools.cms.Metadata import Metadata
from itools.cms.Root import Root


def init(parser, options, target):
    try:
        os.mkdir(target)
    except OSError:
        parser.error('can not create the instance (check permissions)')

    # Create the database
    storage = FileStorage('%s/database.fs' % target)
    database = zodb.Database(storage)

    # Create the config file
    config = RawConfigParser()
    config.add_section('instance')
    if options.root:
        config.set('instance', 'root', options.root)
    config.write(open('%s/config.ini' % target, 'w'))

    # Load the source
    if options.source is None:
        if options.root is None:
            root_class = Root
        else:
            exec('import %s' % options.root)
            exec('root_class = %s' % options.root)
        source = root_class(username='a', password='a').resource
    else:
        source = get_resource(options.source)
        if not isinstance(source, base.Folder):
            parser.error('can not import instance (not a folder)')
        if not source.has_resource('.metadata'):
            parser.error('can not import instance (bad folder)')

    # Initialize the database
    root_resource = database.get_resource('/')
    for name in source.get_resource_names():
        resource = source.get_resource(name)
        root_resource.set_resource(name, resource)
    root_resource.get_transaction().commit()

    # Bravo!
    print 'To start the new instance type:'
    print '  icms.py start %s' % target



def start(parser, options, target):
    if options.source is not None:
        parser.error('option --import not allowed in this context')

    if options.root is not None:
        parser.error('option --root not allowed in this context')

    # Load the config
    config = RawConfigParser()
    config.add_section('instance')
    config.read(['%s/config.ini' % target])

    # Load the root resource
    storage = FileStorage('%s/database.fs' % target)
    database = zodb.Database(storage)
    root_resource = database.get_resource('/')

    # Import the root class if is not the default
    if config.has_option('instance', 'root'):
        exec('import %s' % config.get('instance', 'root'))

    # Load the root handler and start the server
    metadata = root_resource.get_resource('.metadata')
    metadata = Metadata(metadata)
    format = metadata.get_property('format')
    root = Root.build_handler(root_resource, format=format)
    root.name = root.class_title

    # Start the server
    server = Server(root, port=options.port,
                    access_log='%s/access_log' % target,
                    error_log='%s/error_log' % target,
                    pid_file='%s/pid' % target)
    server.start()



if __name__ == '__main__':
    # The command line parser
    usage = ('%prog COMMAND [OPTIONS] TARGET\n'
             '\n'
             'commands:\n'
             '  icms.py init          creates a new instance\n'
             '  icms.py start         starts the web server')
    revision = itools.__arch_revision__
    version = 'itools %s [%s]' % (revision.split('--')[2], revision)
    parser = OptionParser(usage, version=version)
    parser.add_option(
        '-p', '--port', type='int', help='listen to port number')
    parser.add_option(
        '-i', '--import', help='use the SOURCE directory to init the database',
        dest='source')
    parser.add_option(
        '-r', '--root', help='use the ROOT handler class to init the instance')

    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error('incorrect number of arguments')

    command, target = args

    if command == 'init':
        init(parser, options, target)
    elif command == 'start':
        start(parser, options, target)
    else:
        parser.error('unexpected command "%s"' % command)
