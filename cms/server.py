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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import os
from os import remove, rename, listdir
from os.path import isfile, exists, join as join_path
from shutil import copytree, rmtree
import signal

# Import from itools
from itools.handlers.config import Config
from itools.handlers.transactions import get_transaction
from itools import web
from itools.cms.handlers import Metadata
from itools.cms import registry


def ask_confirmation(message):
    print message,
    line = raw_input().strip().lower()
    return line == 'y'



def get_config(target):
    return Config('%s/config.conf' % target)



def get_root(target):
    # Get the root resource
    metadata = Metadata('%s/database/.metadata' % target)
    format = metadata.get_property('format')
    # Build and return the root handler
    cls = registry.get_object_class(format)
    return cls('%s/database' % target)



class Server(web.server.Server):

    def __init__(self, target, address=None, port=None):
        self.target = target.rstrip('/')

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

        # Initialize
        web.server.Server.__init__(self, root, address=address, port=port,
                                   access_log='%s/access_log' % target,
                                   error_log='%s/error_log' % target,
                                   pid_file='%s/pid' % target)

        # The SMTP host
        self.smtp_host = config.get_value('smtp-host')


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


    def start_commit(self):
        open('%s/state' % self.target, 'w').write('START')


    def end_commit_on_success(self):
        target = self.target
        transaction = get_transaction()
        open('%s/state' % target, 'w').write('COMMIT')
        try:
            for handler in transaction:
                uri = handler.uri
                if uri.scheme != 'file':
                    continue
                path = str(uri.path)
                name = handler.name
                if name == '.catalog':
                    dest = str(uri.path.resolve('.catalog.bak'))
                    rmtree(dest)
                    copytree(path, dest)
                elif isfile(path):
                    temp = str(uri.path.resolve('~%s.tmp' % name))
                    rename(temp, path)
                else:
                    for name in listdir(path):
                        if name[0] == '~':
                            temp = join_path(path, name)
                            if name[-4:] == '.add':
                                original = join_path(path, name[1:-4])
                                rename(temp, original)
                            elif name[-4:] == '.del':
                                if isfile(temp):
                                    remove(temp)
                                else:
                                    rmtree(temp)
        except:
            self.log_error()
            # XXX stop instance to introspect
            pid = self.get_pid()
            os.kill(pid, signal.SIGKILL)
        # Finish with the commit
        open('%s/state' % target, 'w').write('OK')
        # Reset the transaction
        transaction.clear()


    def end_commit_on_error(self):
        target = self.target
        transaction = get_transaction()
        open('%s/state' % target, 'w').write('ROLLBACK')
        try:
            for handler in transaction:
                uri = handler.uri
                if uri.scheme != 'file':
                    continue
                path = str(uri.path)
                name = handler.name
                if name == '.catalog':
                    source = str(uri.path.resolve('.catalog.bak'))
                    rmtree(path)
                    copytree(source, path)
                elif isfile(path):
                    temp = str(uri.path.resolve('~%s.tmp' % name))
                    if exists(temp):
                        remove(temp)
                else:
                    for name in listdir(path):
                        if name[0] == '~':
                            temp = join_path(path, name)
                            if name[-4:] == '.add':
                                if isfile(temp):
                                    remove(temp)
                                else:
                                    rmtree(temp)
                            elif name[-4:] == '.del':
                                original = join_path(path, name[1:-4])
                                if exists(original):
                                    if isfile(original):
                                        remove(original)
                                    else:
                                        rmtree(original)
                                rename(temp, original)
        except:
            self.log_error()
            # XXX stop instance to introspect
            pid = self.get_pid()
            os.kill(pid, signal.SIGKILL)
        # Finish with the rollback
        open('%s/state' % target, 'w').write('OK')
        # Reset the transaction
        transaction.clear()
