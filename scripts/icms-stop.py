#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from itools
import itools
from itools.cms.server import Server
from itools.cms.spool import Spool
from itools.cms.utils import kill



def stop(parser, options, target):
    # Stop the Web Server
    server = Server(target)
    pid = server.get_pid()
    if pid is None:
        print '[%s] Web Server not running.' % target
    else:
        kill(pid)
        print '[%s] Web Server shutting down (gracefully)...' % target
    # Stop the Mail Spool
    spool = Spool(target)
    pid = spool.get_pid()
    if pid is None:
        print '[%s] Mail Spool not running.' % target
    else:
        kill(pid)
        print '[%s] Mail Spool shutting down (gracefully)...' % target



if __name__ == '__main__':
    # The command line parser
    usage = '%prog TARGET [TARGET]*'
    version = 'itools %s' % itools.__version__
    description = ('Stops the web server that is publishing the TARGET'
                   ' itools.cms instance (if it is running). Accepts'
                   ' several TARGETs at once, to stop several servers.')
    parser = OptionParser(usage, version=version, description=description)

    options, args = parser.parse_args()
    if len(args) == 0:
        parser.error('incorrect number of arguments')

    # Action!
    for target in args:
        stop(parser, options, target)
