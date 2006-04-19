# -*- coding: ISO-8859-1 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from ConfigParser import RawConfigParser
import os
import sys

# Import from itools
from itools.resources import base, get_resource
from itools import web
from itools.cms.metadata import Metadata
from itools.cms.root import Root


def ask_confirmation(message):
    print message,
    line = sys.stdin.readline()
    line = line.strip().lower()
    return line == 'y'



def get_config(target=None):
    config = RawConfigParser()
    config.add_section('instance')
    if target is not None:
        config.read(['%s/config.ini' % target])
    return config



def get_root(target):
    # Get the root resource
    root_resource = get_resource('%s/database' % target)
    # Find out the format (look into the metadata)
    metadata = root_resource.get_resource('.metadata')
    metadata = Metadata(metadata)
    format = metadata.get_property('format')
    # Build and return the root handler
    return Root.build_handler(root_resource, format=format)



class Server(web.server.Server):

    def __init__(self, target, port=None):
        self.target = target

        # Load the config
        config = get_config(target)

        # Load Python packages and modules
        if config.has_option('instance', 'modules'):
            for name in config.get('instance', 'modules').split():
                name = name.strip()
                exec('import %s' % name)

        # XXX Backwards compatibility (obsolete since 0.13)
        if config.has_option('instance', 'root'):
            exec('import %s' % config.get('instance', 'root'))

        # Load the root handler
        root = get_root(target)
        root.name = root.class_title

        # Find out the port to listen
        if port:
            pass
        elif config.has_option('instance', 'port'):
            port = config.getint('instance', 'port')
        else:
            port = None

        # Initialize
        web.server.Server.__init__(self, root, port=port,
                                   access_log='%s/access_log' % target,
                                   error_log='%s/error_log' % target,
                                   pid_file='%s/pid' % target)


    def get_pid(self):
        try:
            pid = open('%s/pid' % self.target).read()
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

        open('%s/state' % self.target, 'w').write('START')


    def after_commit(self):
        target = self.target
        open('%s/state' % target, 'w').write('END')
        cmd = 'rsync -a --delete %s/database/ %s/database.bak'
        os.system(cmd % (target, target))
        open('%s/state' % target, 'w').write('OK')


    def after_rollback(self):
        target = self.target
        cmd = 'rsync -a --delete %s/database.bak/ %s/database'
        os.system(cmd % (target, target))
        open('%s/state' % target, 'w').write('OK')
