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
from itools import uri
from itools import vfs
from itools.handlers.config import Config
from itools.handlers.transactions import get_transaction
from itools import web
from itools.cms.database import DatabaseFS
from itools.cms.handlers import Metadata
from itools.cms import registry


def ask_confirmation(message):
    print message,
    line = sys.stdin.readline()
    line = line.strip().lower()
    return line == 'y'



def get_config(target):
    return Config('%s/config.conf' % target)



def get_root(target):
    # Get the root resource
    metadata = Metadata(target.resolve2('database/.metadata'))
    format = metadata.get_property('format')
    # Build and return the root handler
    cls = registry.get_object_class(format)
    return cls(target.resolve2('database'))



class Server(web.server.Server):

    def __init__(self, target, address=None, port=None):
        # Set the target under the control of the Database FS
        target = uri.get_absolute_reference2(target)
        target.scheme = 'database'
        self.target = target

        # Load the config
        config = get_config(target)

        # Load Python packages and modules
        modules = config.get_value('modules')
        if modules is not None:
            for name in modules.split():
                name = name.strip()
                exec('import %s' % name)

        # Load the root handler
        root = get_root(target)
        root.name = root.class_title

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

        path = target.path

        # Initialize
        web.server.Server.__init__(self, root, address=address, port=port,
                                   access_log='%s/access_log' % path,
                                   error_log='%s/error_log' % path,
                                   pid_file='%s/pid' % path)

        # The SMTP host
        self.smtp_host = config.get_value('smtp-host')

        # The state file
        self.state_filename = '%s/state' % path

        # The database root
        self.database = target.resolve2('database')


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


    def before_commit(self, transaction):
        for handler in list(transaction):
            if hasattr(handler, 'before_commit'):
                handler.before_commit()


    def start_commit(self):
        open(self.state_filename, 'w').write('START')
        # Create the commit folder
        path = self.target.path.resolve2('~database/log')
        path = str(path)
        vfs.make_file(path)


    def end_commit_on_success(self):
        state_filename = self.state_filename
        open(state_filename, 'w').write('END')
        DatabaseFS.commit_transaction(self.database)
        # Finish with the backup
        open(state_filename, 'w').write('OK')
        # Clean the transaction
        get_transaction().clear()


    def end_commit_on_error(self):
        DatabaseFS.rollback_transaction(self.database)
        # Finish with the rollback
        open(self.state_filename, 'w').write('OK')
