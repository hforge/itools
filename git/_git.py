# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from subprocess import CalledProcessError

# Import from itools
from itools.core import send_subprocess
from itools.datatypes import ISODateTime


class WorkTree(object):

    def __init__(self, path):
        self.path = path


    def _send_subprocess(self, cmd):
        return send_subprocess(cmd, path=self.path)


    #######################################################################
    # Public API
    #######################################################################
    def git_add(self, *args):
        if args:
            self._send_subprocess(['git', 'add'] + list(args))


    def git_commit(self, message, author=None, date=None, quiet=False,
                   all=False):
        cmd = ['git', 'commit', '-m', message]
        if author:
            cmd.append('--author=%s' % author)
        if date:
            date = ISODateTime.encode(date)
            cmd.append('--date=%s' % date)
        if quiet:
            cmd.append('-q')
        if all:
            cmd.append('-a')

        try:
            self._send_subprocess(cmd)
        except CalledProcessError, excp:
            # Avoid an exception for the 'nothing to commit' case
            # FIXME Not reliable, we may catch other cases
            if excp.returncode != 1:
                raise
