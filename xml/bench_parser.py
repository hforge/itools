# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import time

# Import from itools
from itools.xml import XMLParser

if __name__ == '__main__':

    data = open('bench_parser.xml').read()
    while 1:
        rounds = 100000
        r = range(rounds)
        t0 = time.clock()
        for i in r:
            for event, value, line_number in XMLParser(data):
                pass
        t1 = time.clock()
        print "Average time : %f ms" % ((t1 - t0) * (1000. / float(rounds)))
