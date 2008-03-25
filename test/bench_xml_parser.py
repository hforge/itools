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
from timeit import Timer


test = "for event in XMLParser(data): pass"
setup = """
from itools.xml import XMLParser
data = open('bench_xml_parser.xml').read()
"""


if __name__ == '__main__':
    timer = Timer(test, setup)
    rounds = 10000

    best = 3600.0
    for i in range(5):
        t = timer.timeit(rounds)
        # In miliseconds
        t = 1000 * (t / rounds)
        print "Loop %s: %0.3f ms" % (i, t)
        if t < best:
            best = t

    # Best time in miliseconds
    print
    print "Best time: %0.3f ms" % best
