# -*- coding: UTF-8 -*-
# Copyright (C) 2010 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2010-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
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
from sys import version_info

# Import from pygobject
from gobject import MainLoop, timeout_add_seconds


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



if version_info[:2] == (2, 6):
    # Python 2.6
    def total_seconds(td):
        if type(td) is int:
            return td
        seconds = (td.seconds + td.days * 24 * 3600)
        return (td.microseconds + seconds * 10**6) / 10**6
else:
    # Python 2.7
    def total_seconds(td):
        if type(td) is int:
            return td
        return int(td.total_seconds())



def callback_wrapper(callback, interval, *args):
    """This function wraps the actual callback. It allows the callback to
    return a timedelta object specifying the interval for the next try.
    Otherwise it accepts the standard return values (True/Flase).
    """
    new_interval = callback(*args)
    # Case 1: stop or continue with the same interval
    if type(new_interval) is bool:
        return new_interval

    # Case 2: change the interval
    new_interval = total_seconds(new_interval)
    if new_interval == interval:
        return True

    timeout_add_seconds(new_interval, callback_wrapper,
                        callback, new_interval, *args)
    return False



def cron(callback, interval, *args):
    """Add new cronjob.

       callback -- the callable to run.

       interval -- timedelta specifying when the cronjob will be called.

       args -- payload that will be passed to the callable on each call.
    """
    interval = total_seconds(interval)
    if interval == 0:
        error = "cron: your timedelta has a too small resolution (< 1s)"
        raise ValueError, error

    timeout_add_seconds(interval, callback_wrapper, callback, interval, *args)
