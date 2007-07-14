# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Luis A. Belmar Letelier <luis@itaapy.com>
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
import unittest
from unittest import TestCase

# Import from itools
from itools.datatypes import Unicode
from itools.handlers import get_handler, Python, Table
from itools.handlers.table import unfold_lines



class FolderTestCase(TestCase):

    def test_has_handler(self):
        handler = get_handler('tests')
        self.assertEqual(handler.has_handler('hello.txt'), True)
       


class TextTestCase(TestCase):
    
    def test_load_file(self):
        handler = get_handler('tests/hello.txt')
        self.assertEqual(handler.data, u'hello world\n')



##########################################################################
# The Table handler
##########################################################################

simple_table = """id:0/0
ts:2007-07-13T17:19:21

id:1/0
ts:2007-07-14T16:43:49
"""

agenda_file = """id:0/0
ts:2007-07-13T17:19:21
firstname:Karl
lastname:Marx

id:1/0
ts:2007-07-14T16:43:49
firstname:Jean-Jacques
lastname:Rousseau
"""


class Agenda(Table):
    schema = {'firstname': Unicode(index='text'),
              'lastname': Unicode}


class TableTestCase(TestCase):

    def test_unfolding(self):
        """Test unfolding lines."""
        input = (
            'BEGIN:VCALENDAR\n'
            'VERSION:2.0\n'
            'BEGIN:VEVENT\n'
            'UID:581361a0-1dd2-11b2-9a42-bd3958eeac9a\n'
            'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0\n'
            'DTSTART;VALUE=DATE:20050530\n'
            'DTEND;VALUE=DATE:20050531\n'
            'DTSTAMP:20050601T074604Z\n'
            'DESCRIPTION:opps !!! this is a really big information, ..., '
            'but does it change anything \n'
            ' in reality ?? We should see a radical change in the next \n'
            ' 3 months, shouldn\'t we ???\\nAaah !!!\n' )

        expected = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'BEGIN:VEVENT',
            'UID:581361a0-1dd2-11b2-9a42-bd3958eeac9a',
            'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0',
            'DTSTART;VALUE=DATE:20050530',
            'DTEND;VALUE=DATE:20050531',
            'DTSTAMP:20050601T074604Z',
            'DESCRIPTION:opps !!! this is a really big information, ..., but'
            ' does it change anything in reality ?? We should see a radical'
            ' change in the next 3 months, shouldn\'t we ???\\nAaah !!!']

        output = unfold_lines(input)

        i = 0
        for line in output:
            self.assertEqual(line, expected[i])
            i = i + 1


    def test_de_serialize(self):
        table = Table(string=simple_table)
        self.assertEqual(table.to_str(), simple_table)


    def test_search(self):
        agenda = Agenda(string=agenda_file)
        ids = [ x.id for x in agenda.search(firstname=u'Jean') ]
        self.assertEqual(ids, [1])



if __name__ == '__main__':
    unittest.main()
