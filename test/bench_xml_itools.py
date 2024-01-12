#!/usr/bin/env python
# Copyright (C) 2008 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2008-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2009 Aurélien Ansel <camumus@gmail.com>
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
import sys

# Import from itools
from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT


if __name__ == '__main__':
    # Read input parameters
    filename = sys.argv[1]
    nb_repeat = int(sys.argv[2])

    # Open the test file
    with open(filename) as test_file:

        # Loop
        while nb_repeat > 0:
            nb_repeat -= 1
            # Parse
            parser = XMLParser(test_file)
            try:
                for type, value, line in parser:
                    if type == START_ELEMENT:
                        pass
                    elif type == END_ELEMENT:
                        pass
            except Exception:
                # Error
                test_file.close()
                exit(1)
            # Again
            test_file.seek(0)

    # Ok

