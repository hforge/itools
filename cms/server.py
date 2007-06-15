# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import os
import sys

# Import from itools
from itools.uri import get_absolute_reference2
from itools import vfs
from itools.catalog import Catalog
from itools.handlers import Config, get_transaction
from itools.web import Server as BaseServer
from itools.cms.database import DatabaseFS
from itools.cms.handlers import Metadata
from itools.cms import registry
from catalog import get_to_index, get_to_unindex


def ask_confirmation(message):
    sys.stdout.write(message)
    sys.stdout.flush()
    line = sys.stdin.readline()
    line = line.strip().lower()
    return line == 'y'



def get_config(target):
    return Config('%s/config.conf' % target)



def get_root_class(root):
    # Get the root resource
    metadata = Metadata(root.resolve2('.metadata'))
    format = metadata.get_property('format')
    # Build and return the root handler
    return registry.get_object_class(format)



class Server(BaseServer):

    def __init__(self, target, address=None, port=None):
        target = get_absolute_reference2(target)
        self.target = target

        # Load the config
        config = get_config(target)

        # Load Python packages and modules
        modules = config.get_value('modules')
        if modules is not None:
            for name in modules.split():
                name = name.strip()
                exec('import %s' % name)

        # Find out the IP to listen to
        if address:
            pass
        else:
            address = config.get_value('address')

        # Find out the port to listen
        if port:
            pass
        else:
            port = config.get_value('port')
            if port is not None:
                port = int(port)

        # The database
        root = target.resolve2('database')
        cls = get_root_class(root)
        database = DatabaseFS(target.path, cls=cls)
        self.database = database
        # The catalog
        self.catalog = Catalog('%s/catalog' % target)

        # Fix the root's name
        root = database.root
        root.name = root.class_title

        # Initialize
        path = target.path
        BaseServer.__init__(self, root, address=address, port=port,
                            access_log='%s/access_log' % path,
                            error_log='%s/error_log' % path,
                            pid_file='%s/pid' % path)

        # The SMTP host
        self.smtp_host = config.get_value('smtp-host')


    def get_pid(self):
        try:
            pid = open('%s/pid' % self.target.path).read()
        except IOError:
            return None

        pid = int(pid)
        try:
            # XXX This only works on Unix
            os.getpgid(pid)
        except OSError:
            return None

        return pid


    #######################################################################
    # Override
    #######################################################################
    def get_databases(self):
        return [self.database, self.catalog]


    def before_commit(self):
        catalog = self.catalog
        # Unindex Handlers
        to_unindex = get_to_unindex()
        for handler in to_unindex:
            catalog.unindex_document(handler)
        to_unindex.clear()

        # Index Handlers
        to_index = get_to_index()
        for handler in to_index:
            catalog.index_document(handler)
        to_index.clear()

        # XXX Versioning
        transaction = get_transaction()
        for handler in list(transaction):
            if hasattr(handler, 'before_commit'):
                handler.before_commit()

