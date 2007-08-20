#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
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
from optparse import OptionParser
import os
import sys

# Import from itools
import itools
from itools import vfs
from itools.cms.server import Server
from itools.cms.spool import Spool



def start(parser, options, target):
    # Check wether the instance uses a backup database (XXX remove for 0.17).
    folder = vfs.open(target)
    if folder.exists('database/.catalog'):
        print ('The database must be updated, type:')
        print
        print '    $ icms-update.py <instance>'
        print
        return

    # Check for database consistency
    if vfs.exists('%s/database.commit' % target):
        print 'The database is not in a consistent state, to fix it up type:'
        print
        print '    $ icms-restore.py <instance>'
        print
        return

    # Set-up the servers
    server = Server(target, address=options.address, port=options.port)
    spool = Spool(target)

    # Check the instance is up-to-date
    root = server.root
    if root.get_property('version') < root.class_version:
        print 'The instance is not up-to-date, please type:'
        print
        print '    $ icms-update.py <instance>'
        print
        return

    # Check the server is not running
    pid = server.get_pid()
    if pid is not None:
        print '%s: The server is already running.' % target
        return

    print '%s: Listen port %s' % (target, server.port)

    # Debugging mode
    if options.debug is False:
        if sys.platform.startswith('win'):
            # TODO Implement it for Windows
            msg = u'Unable to daemonize on Windows... Please use the option -d'
            raise NotImplementedError, msg
        # Detach from the console (this code derives from the Python
        # Cookbook, see section "Forking a Daemon on Unix").
        pid = os.fork()
        # The father exits
        if pid > 0:
            return
        # The child becomes its own session leader with its own tty
        # that doesn't exist for now but may be affected later
        os.setsid()
        # So forking again to decouple for good
        pid = os.fork()
        # the new father exits
        if pid > 0:
            sys.exit(0)
        # Redirect standard file descriptors to '/dev/null' (see Bugzilla #284)
        devnull = os.open(os.devnull, os.O_RDWR)
        sys.stdin.close()
        os.dup2(devnull, 0)
        sys.stdout.flush()
        os.dup2(devnull, 1)
        sys.stderr.flush()
        os.dup2(devnull, 2)

    pid = os.fork()
    if pid > 0:
        # Start the Web Server
        server.start()
    else:
        # Start the Mail Spool
        spool.start()



if __name__ == '__main__':
    # The command line parser
    usage = ('%prog [OPTIONS] TARGET\n'
             '       %prog TARGET [TARGET]*')
    version = 'itools %s' % itools.__version__
    description = ('Starts a web server that publishes the TARGET itools.cms'
                   ' instance to the world. If several TARGETs are given, one'
                   ' server will be started for each one (in this mode no'
                   ' options are available).')
    parser = OptionParser(usage, version=version, description=description)
    parser.add_option(
        '-d', '--debug', action="store_true", default=False,
        help="start the server on debug mode (don't detach from the console)")
    parser.add_option(
        '-a', '--address', help='listen to IP ADDRESS')
    parser.add_option(
        '-p', '--port', type='int', help='listen to PORT number')

    options, args = parser.parse_args()
    n_args = len(args)
    if n_args == 0:
        parser.error('The TARGET argument is missing.')
    elif n_args == 1:
        pass
    elif options.address or options.debug or options.port:
        parser.error(
            'Options are not available when starting several servers at once.')

    # Action!
    for target in args:
        start(parser, options, target)
