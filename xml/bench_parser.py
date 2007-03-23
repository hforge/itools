# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import profile
from time import time

# Import from itools
import itools
from itools.xml import Document, Parser



# itools.xml.parser: 0.0062
##data = open('bench_parser.xml').read()
##t0 = time()
##for event, value, line_number in Parser(data):
##    pass
##print time() - t0


if __name__ == '__main__':
    if 1:
        # The old parser: 0.0234 (reference time)
        # The new parser: 0.0309
        doc = Document('bench_parser.xml')
        t0 = time()
        doc.load_state()
        t1 = time()
        print itools.__version__, t1 - t0
    else:
        data = open('bench_parser.xml').read()
        profile.run('list(Parser(data))')
