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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

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
from itools.handlers import transactions
from itools.web.server import Server
from itools.cms.Handler import Handler
from itools.cms.Metadata import Metadata
from itools.cms.Root import Root
from itools.cms.versioning import VersioningAware



def get_config(target=None):
    config = RawConfigParser()
    config.add_section('instance')
    if target is not None:
        config.read(['%s/config.ini' % target])
    return config


def get_database(target):
    storage = FileStorage('%s/database.fs' % target)
    return zodb.Database(storage)


def get_root(database):
    # Get the root resource
    root_resource = database.get_resource('/')
    # Find out the format (look into the metadata)
    metadata = root_resource.get_resource('.metadata')
    metadata = Metadata(metadata)
    format = metadata.get_property('format')
    # Build and return the root handler
    return Root.build_handler(root_resource, format=format)



def init(parser, options, target):
    try:
        os.mkdir(target)
    except OSError:
        parser.error('can not create the instance (check permissions)')

    # Create the config file
    config = get_config()
    if options.root:
        config.set('instance', 'root', options.root)
    if options.port:
        config.set('instance', 'port', options.port)
    config.write(open('%s/config.ini' % target, 'w'))

    # Create the database
    database = get_database(target)

    # Load the source
    if options.source is None:
        if options.root is None:
            root_class = Root
        else:
            exec('import %s' % options.root)
            exec('root_class = %s.Root' % options.root)
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

    # Index and archive everything (only for new instances, not imported)
    if options.source is None:
        root = root_class(root_resource)
        catalog = root.get_handler('.catalog')
        for handler, context in root.traverse2():
            abspath = handler.get_abspath()
            if handler.name.startswith('.'):
                context.skip = True
            elif abspath == '/ui':
                context.skip = True
            elif isinstance(handler, Handler):
                catalog.index_document(handler)
                if isinstance(handler, VersioningAware):
                    handler.add_to_archive()

        transaction = transactions.get_transaction()
        transaction.commit()

    # Bravo!
    print 'To start the new instance type:'
    print '  %s start %s' % (parser.get_prog_name(), target)



def start(parser, options, target):
    # Load the config
    config = get_config(target)

    # Import the root class if is not the default
    if config.has_option('instance', 'root'):
        exec('import %s' % config.get('instance', 'root'))

    # Load the root handler
    database = get_database(target)
    root = get_root(database)
    root.name = root.class_title

    # Start the server
    if options.port:
        port = options.port
    elif config.has_option('instance', 'port'):
        port = config.getint('instance', 'port')
    else:
        port = None

    server = Server(root, port=port, access_log='%s/access_log' % target,
                    error_log='%s/error_log' % target,
                    pid_file='%s/pid' % target)
    server.start()


def update(parser, options, target):
    # Load the config
    config = get_config(target)

    # Import the root class if is not the default
    if config.has_option('instance', 'root'):
        exec('import %s' % config.get('instance', 'root'))

    # Load the root resource
    database = get_database(target)
    root = get_root(database)

    instance_version = root.get_property('version')
    class_version = root.class_version
    if instance_version == class_version:
        print 'The instance is up-to-date (version: %s).' % instance_version
    elif instance_version > class_version:
        print 'WARNING: the instance (%s) is newer! than the class (%s)' \
              % (instance_version, class_version)
    else:
        print 'Update instance from version %s to version %s (y/N)? ' \
              % (instance_version, class_version),
        line = sys.stdin.readline()
        line = line.strip().lower()
        if line == 'y':
            print 'Updating...'
            root.update()


def pack(parser, options, target):
    database = get_database(target).database
    print 'Packing...', 
    database.pack()
    print 'done.'



if __name__ == '__main__':
    # The command line parser
    usage = ('%prog COMMAND [OPTIONS] TARGET\n'
             '\n'
             'commands:\n'
             '  %prog init          creates a new instance\n'
             '  %prog start         starts the web server\n'
             '  %prog update        updates the instance (if needed)\n'
             '  %prog pack          packs the database')
    revision = itools.__arch_revision__
    version = 'itools %s [%s]' % (revision.split('--')[2], revision)
    parser = OptionParser(usage, version=version)
    parser.add_option(
        '-p', '--port', type='int', help='listen to port number')
    parser.add_option(
        '-s', '--source', help='use the SOURCE directory to init the database')
    parser.add_option(
        '-r', '--root', help='use the ROOT handler class to init the instance')

    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error('incorrect number of arguments')

    command_name, target = args

    # Mapping from command name to command function and list of allowed options
    commands = {'init': (init, ['source', 'root', 'port']),
                'start': (start, ['port']),
                'update': (update, []),
                'pack': (pack, [])}

    # Check wether the command exists
    if command_name not in commands:
        parser.error('unexpected command "%s"' % command_name)

    # Check wether a forbidden option (in this context) was used
    command, allowed_options = commands[command_name]
    for key, value in options.__dict__.items():
        if key not in allowed_options and value is not None:
            parser.error('the command "%s" does not accept the option -%s/--%s'
                         % (command_name, key[0], key))

    # Action!
    command(parser, options, target)
