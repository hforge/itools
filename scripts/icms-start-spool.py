#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Taverne Sylvain <sylvain@itaapy.com>
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

# Import from standard library
from optparse import OptionParser
import os
import sys
# Import from itools
import itools
from itools.cms.spool import Spool

def start(optios, target):
    spool = Spool(target)
    pid = spool.get_pid()
    if pid is not None:
        print 'The spool is already running.'
        return

    if options.debug is False:
        # Redirect standard file descriptors to '/dev/null'
        devnull = os.open(os.devnull, os.O_RDWR)
        sys.stdin.close()
        os.dup2(devnull, 0)
        sys.stdout.flush()
        os.dup2(devnull, 1)
        sys.stderr.flush()
        os.dup2(devnull, 2)
    spool.start()


if __name__ == '__main__':
    # The command line parser
    usage = ('%prog TARGET')
    version = 'itools %s' % itools.__version__
    description = ('Starts a spool server')
    parser = OptionParser(usage, version=version, description=description)
    parser.add_option('-d', '--debug', action="store_true", default=False,
                      help="Start the server on debug mode.")

    options, args = parser.parse_args()
    if len(args) == 0:
        parser.error('The TARGET argument is missing.')

    # Start the spool
    start(options, args[0])
