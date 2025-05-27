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

import asyncio
import datetime
import typing


def total_seconds(td: typing.Union[int, datetime.timedelta]) -> int:
    """Convert timedelta or int to total seconds as int."""
    if isinstance(td, int):
        return td
    return int(td.total_seconds())


async def _cron(
    callback: typing.Callable[[], typing.Optional[typing.Union[int, datetime.timedelta]]],
    interval: typing.Union[int, datetime.timedelta]
):
    """Internal async cron loop."""
    while True:
        interval = total_seconds(interval)
        await asyncio.sleep(interval)
        interval = await callback()  # Get new interval from callback
        if not interval:
            break


def cron(
    callback: typing.Callable[[], typing.Optional[typing.Union[int, datetime.timedelta]]],
    interval: typing.Union[int, datetime.timedelta]
):
    """
    Add new async cronjob.

    Args:
        callback: The callable to run, which can return a new interval or None to stop
        interval: Either timedelta or seconds (int) specifying when to call the callback

    Raises:
        ValueError: If interval is 0
    """
    if total_seconds(interval) == 0:
        raise ValueError("async_cron: interval has too small resolution (< 1s)")

    # Create task but don't await it (fire-and-forget)
    asyncio.create_task(_cron(callback, interval))
