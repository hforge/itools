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
from ConfigParser import RawConfigParser
import os
import subprocess
import sys

# Import from itools
from itools import vfs
from itools.handlers.Folder import Folder
from itools.handlers.transactions import get_transaction
from itools import web
from itools.cms.handlers import Metadata
from itools.cms import registry
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

        # Find out the IP to listen to
        if address:
            pass
        elif config.has_option('instance', 'address'):
            address = config.get('instance', 'address')
        else:
            address = None

        # Find out the port to listen
        if port:
            pass
        elif config.has_option('instance', 'port'):
            port = config.getint('instance', 'port')
        else:
            port = None

        # Initialize
        web.server.Server.__init__(self, root, address=address, port=port,
                                   access_log='%s/access_log' % target,
                                   error_log='%s/error_log' % target,
                                   pid_file='%s/pid' % target)

        # The SMTP host
        if config.has_option('instance', 'smtp-host'):
            self.smtp_host = config.get('instance', 'smtp-host')
        else:
            self.smtp_host = None


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
        abspaths = [ str(x.uri.path) for x in transaction
                     if x.uri.scheme == 'file' ]
        abspaths.sort()
        open('%s/state' % target, 'w').write('END')
        try:
            a, b = '%s/database' % target, '%s/database.bak' % target
            catalog_path = '%s/.catalog' % a
            for src in abspaths:
                dst = src.replace(a, b, 1)
                if src.endswith(catalog_path):
                    # XXX Hack for the catalog
                    subprocess.call(['rsync', '-a', '--delete', src + '/', dst])
                elif os.path.isdir(src):
                    src_files = set(os.listdir(src))
                    dst_files = set(os.listdir(dst))
                    # Remove
                    for filename in dst_files - src_files:
                        vfs.remove('%s/%s' % (dst, filename))
                    # Add
                    for filename in src_files - dst_files:
                        srcfile = '%s/%s' % (src, filename)
                        dstfile = '%s/%s' % (dst, filename)
                        vfs.copy(srcfile, dstfile)
                else:
                    open(dst, 'w').write(open(src).read())
        except:
            # Something wrong? Fall to more safe (and slow) rsync, and log
            # the error.
            self.log_error()
            subprocess.call(['rsync', '-a', '--delete',
                             '%s/database/' % target,
                             '%s/database.bak' % target])

        # Finish with the backup
        open('%s/state' % target, 'w').write('OK')
        # Clean the transaction
        transaction.clear()


    def end_commit_on_error(self):
        target = self.target
        subprocess.call(['rsync', '-a', '--delete',
                         '%s/database.bak/' % target,
                         '%s/database' % target])
        open('%s/state' % target, 'w').write('OK')
