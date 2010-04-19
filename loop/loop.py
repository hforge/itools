# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from cProfile import runctx
from os import getpid, remove as remove_file
from signal import signal, SIGINT, SIGTERM

# Import from pygobject
from gobject import MainLoop


class Loop(MainLoop):

    def __init__(self, pid_file=None, profile=None):
        super(Loop, self).__init__()
        self.pid_file = pid_file
        self.profile = profile


    def run(self):
        # Stop signals
        signal(SIGINT, self.stop) # TODO Implement graceful stop
        signal(SIGTERM, self.stop)

        # Graceful stop
        if self.pid_file:
            pid = getpid()
            open(self.pid_file, 'w').write(str(pid))

        # Run
        profile = self.profile
        if profile:
            runctx("super(Loop, self).run()", globals(), locals(), profile)
        else:
            super(Loop, self).run()


    def stop(self, signum, frame):
        print 'Shutting down the server...'
        self.quit()


    def quit(self):
        super(Loop, self).quit()
        if self.pid_file:
            remove_file(self.pid_file)
