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
from itools.handlers.Folder import Folder
from itools.handlers.transactions import get_transaction
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


    def start_commit(self):
        open('%s/state' % self.target, 'w').write('START')


    def end_commit_on_success(self):
        target = self.target
        db = '%s/database' % target
        db2 = '%s/database.bak' % target

        transaction = get_transaction()

        open('%s/state' % target, 'w').write('END')

        abspaths = []
        for handler in transaction:
            if handler.real_handler is not None:
                handler = handler.real_handler
            abspaths.append(handler.get_abspath())
        abspaths.sort()

        for abspath in abspaths:
            src = '%s%s' % (db, abspath)
            dst = '%s%s' % (db2, abspath)

            if os.path.isdir(src):
                src_files = set(os.listdir(src))
                dst_files = set(os.listdir(dst))
                # Remove
                for filename in dst_files - src_files:
                    filename = '%s/%s' % (dst, filename)
                    if os.path.isdir(filename):
                        os.system('rm -r %s' % filename)
                    else:
                        os.remove(filename)
                # Add
                for filename in src_files - dst_files:
                    srcfile = '%s/%s' % (src, filename)
                    dstfile = '%s/%s' % (dst, filename)
                    if os.path.isdir(srcfile):
                        os.system('cp -r %s %s' % (srcfile, dstfile))
                    else:
                        open(dstfile, 'w').write(open(srcfile).read())
                # Different. XXX Could not need this if IIndex (itools.catalog)
                # was not a so special handler (the folder keeps the data
                # structure for the files).
                for filename in src_files & dst_files:
                    srcfile = '%s/%s' % (src, filename)
                    dstfile = '%s/%s' % (dst, filename)
                    srctime = os.stat(srcfile).st_mtime
                    dsttime = os.stat(dstfile).st_mtime
                    if srctime > dsttime:
                        # Remove
                        if os.path.isdir(dstfile):
                            os.system('rm -r %s' % dstfile)
                        else:
                            os.remove(dstfile)
                        # Copy
                        if os.path.isdir(srcfile):
                            os.system('cp -r %s %s' % (srcfile, dstfile))
                        else:
                            open(dstfile, 'w').write(open(srcfile).read())
            else:
                open(dst, 'w').write(open(src).read())

        # Finish with the backup
        open('%s/state' % target, 'w').write('OK')
        # Clean the transaction
        transaction.clear()


    def end_commit_on_error(self):
        target = self.target
        cmd = 'rsync -a --delete %s/database.bak/ %s/database'
        os.system(cmd % (target, target))
        open('%s/state' % target, 'w').write('OK')
