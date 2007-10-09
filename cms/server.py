# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from os import fdopen
import sys
from tempfile import mkstemp

# Import from itools
from itools.uri import get_absolute_reference2
from itools import vfs
from itools.catalog import Catalog
from itools.handlers import Config, Database
from itools.web import Server as BaseServer
from handlers import Metadata
import registry
from catalog import get_to_index, get_to_unindex
from website import WebSite


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
        database = Database('%s/database.commit' % target.path)
        self.database = database
        # The catalog
        self.catalog = Catalog('%s/catalog' % target)

        # Build the root handler
        root = target.resolve2('database')
        cls = get_root_class(root)
        root = cls(root)
        root.database = database
        root.name = root.class_title

        # Initialize
        path = target.path
        BaseServer.__init__(self, root, address=address, port=port,
                            access_log='%s/access_log' % path,
                            error_log='%s/error_log' % path,
                            pid_file='%s/pid' % path)


    def get_pid(self):
        try:
            pid = open('%s/pid' % self.target.path).read()
        except IOError:
            return None

        pid = int(pid)
        # Check if PID exist
        if sys.platform[:3] == 'win':
            try:
                import win32api
                win32api.OpenProcess(1, False, pid)
            except:
                return None
        else:
            try:
                from os import getpgid
                getpgid(pid)
            except OSError:
                return None

        return pid


    def send_email(self, message):
        spool = self.target.resolve2('spool')
        spool = str(spool.path)
        tmp_file, tmp_path = mkstemp(dir=spool)
        file = fdopen(tmp_file, 'w')
        try:
            file.write(message.as_string())
        finally:
            file.close()


    #######################################################################
    # Override
    #######################################################################
    def get_site_root(self, hostname):
        root = self.root

        sites = [root]
        for site in root.search_handlers(handler_class=WebSite):
            sites.append(site)

        for site in sites:
            if hostname in site.get_property('ikaaro:vhosts'):
                return site

        return root


    def get_databases(self):
        return [self.database, self.catalog]


    def abort_transaction(self, context):
        # Clean the index/unindex queues
        get_to_index().clear()
        get_to_unindex().clear()

        BaseServer.abort_transaction(self, context)


    def before_commit(self):
        catalog = self.catalog
        # Unindex Handlers
        to_unindex = get_to_unindex()
        for path in to_unindex:
            catalog.unindex_document(path)
        to_unindex.clear()

        # Index Handlers
        to_index = get_to_index()
        for handler in to_index:
            catalog.index_document(handler)
        to_index.clear()

        # XXX Versioning
        transaction = self.database.changed
        for handler in list(transaction):
            if hasattr(handler, 'before_commit'):
                handler.before_commit()

