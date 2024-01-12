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

# Import from gevent
from gevent import sleep, Greenlet


def total_seconds(td):
    if type(td) is int:
        return td
    return int(td.total_seconds())


def _cron(callback, interval):
    while True:
        interval = total_seconds(interval)
        sleep(interval)
        interval = callback()
        if not interval:
            break


def cron(callback, interval):
    """Add new cronjob.
       callback -- the callable to run.
       interval -- timedelta specifying when the cronjob will be called.
    """
    if interval == 0:
        error = "cron: your timedelta has a too small resolution (< 1s)"
        raise ValueError(error)
    Greenlet.spawn(_cron, callback, interval)
