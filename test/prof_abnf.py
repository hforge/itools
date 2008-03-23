# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from profile import run as profile
from timeit import Timer

# Import from itools
from itools.uri.parsing import parse_uri


def bench():
    """Benchmark the speed of itools.abnf using "urlparse.urlsplit" as
    reference.
    """
    # itools
    timer = Timer("parse_uri('http://example.com/')",
                  "from itools.uri.parsing import parse_uri")
    a = timer.timeit(1)
    # stdlib
    timer = Timer("urlsplit('http://example.com/')",
                  "from urlparse import urlsplit")
    b = timer.timeit(1)

    print 'itools:', a
    print 'stdlib:', b
    print
    print 'itools %d times slower than stdlib' % (a/b)



if __name__ == '__main__':
    bench()
#    profile('parse_uri("http://example.com/")')
