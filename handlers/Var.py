# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


"""
This module implements a parser for the Apache's type map files.
For now we don't support the 'Body' keyword. See the documentation
in Apache for the module 'mod_negotiation'.
"""


# Import from itools.handlers
from File import File
from Text import Text



class Record(object):
    def __init__(self, uri=None, type=None, language=None, encoding=None,
                 length=None):
        self.uri = uri
        self.type = type
        self.language = language
        self.encoding = encoding
        self.length = length


    def set_header(self, header, line=0):
        """
        Parse a header line and set the value.
        """
        # XXX We should do additional checks, like invalid values or repeated
        # headers.
        # XXX We should do further parsing for the value.

        header = header.split(':', 1)
        if len(header) != 2:
            raise ValueError, 'syntax error at line %d' % line
        keyword, value = header
        keyword = keyword.strip().lower()
        value = value.strip()

        if keyword == 'uri':
            self.uri = value
        elif keyword == 'content-type':
            self.type = value
        elif keyword == 'content-language':
            self.language = value
        elif keyword == 'content-encoding':
            self.encoding = value
        elif keyword == 'content-length':
            self.length = value
        else:
            raise ValueError, \
                  'unsupported header %s at line %d' % (keyword, line)


    def __unicode__(self):
        s = u'URI: %s\n' % self.uri
        if self.type:
            s += u'Content-Type: %s\n' % self.type
        if self.language:
            s += u'Content-Language: %s\n' % self.language
        if self.encoding:
            s += u'Content-Encoding: %s\n' % self.encoding
        if self.length:
            s += u'Content-Length: %s\n' % self.length
        return s
        
        



class Var(Text):

    #######################################################################
    # Parsing
    #######################################################################
    def _load(self):
        File._load(self)
        self.records = []

        i = 1
        state = 0
        for line in self._data.split('\n'):
            line = line.strip()

            if line.startswith('#'):
                continue

            if state == 0:
                if line:
                    record = Record()
                    record.set_header(line)
                    state = 1
            else:
                if line:
                    record.set_header(line)
                else:
                    self.records.append(record)
                    state = 0

            i = i + 1

        # Remove data
        del self._data


    ########################################################################
    # Skeleton
    ########################################################################
    def get_skeleton(self, uri=None, language='en', mimetype='text/plain'):
        data = 'URI: %s\n' % uri
        data += 'Content-Language: %s\n' % language
        data += 'Content-Type: %s; charset=UTF-8\n' % mimetype
        return data


    #######################################################################
    # API
    #######################################################################
    def __unicode__(self):
        return '\n'.join([ unicode(x) for x in self.records ])
