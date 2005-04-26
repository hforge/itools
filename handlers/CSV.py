# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


# Import from the Standard Library
import csv

# Import from itools
from Text import Text



def parse(data, schema=None):
    encoding = Text.guess_encoding(data)
    # Build the reader
    if data:
        dialect = csv.Sniffer().sniff(data[:1000])
        reader = csv.reader(data.splitlines(), dialect)
    else:
        reader = csv.reader(data.splitlines())
    # Add type
    if schema is None:
        for line in reader:
            yield [ unicode(x, encoding) for x in line ]
    else:
        for line in reader:
            yield [ schema[i].decode(value)
                    for i, value in enumerate(line) ]


class CSV(Text):

    class_mimetypes = ['text/comma-separated-values', 'text/csv']


    schema = None


    #########################################################################
    # Parsing
    #########################################################################
    def _load_state(self, resource):
        data = resource.read()

##        data = [ x.strip() for x in data.splitlines() ]
##        data = [ x for x in data if x ]

        self.lines = list(parse(data, self.schema))
        self._encoding = self.guess_encoding(data)


    #########################################################################
    # API
    #########################################################################
    def to_unicode(self, encoding=None):
        lines = []
        for line in self.lines:
            line = [ u'"%s"' % x for x in line ]
            lines.append(u','.join(line))
        return u'\n'.join(lines)


CSV.register_handler_class(Text)
