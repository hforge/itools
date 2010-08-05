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
from gobject import MainLoop, timeout_add_seconds, idle_add


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



def _cron_mgr(callback, interval):
    ret = callback()
    if ret:
        timeout_add_seconds(interval, callback)
    return False



def _total_seconds(td):
    # FIXME This function exists in python >= 2.7
    return ( (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6)
              / 10**6 )



def cron(callback, interval, first_call_delay=None):
    """Set a new event.

       callback is a callable. It must return True (continue) or False (stop).

       interval and first_call_delay are datetime.timedelta objects. Their
       resolutions must be the second.

       first_call_delay can be None. In this case, callback is called
       immediately but when the application is idle. So first_call_delay=None
       and first_call_delay=0s have not exactly the same meaning.
    """
    interval = _total_seconds(interval)
    if not interval > 0:
        raise ValueError, ("cron: your timedelta has a too small resolution "
                           "(< 1s)")

    if first_call_delay is None:
        idle_add(_cron_mgr, callback, interval)
    else:
        first_call_delay = _total_seconds(first_call_delay)
        timeout_add_seconds(first_call_delay, _cron_mgr, callback, interval)
