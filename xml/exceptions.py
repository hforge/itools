# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


class XMLError(Exception):
    """
    The expat parser checks the document to be well formed, if it is not
    the ExpatError exception is raised.

    The XMLError exception (or a subclass of it) should be raised when
    the document does not conform to an schema. For an example see how
    it is used by the STL language.

    Note that right now we don't automatically check against DTD's or
    schemas (that's something to do: XXX), so your namespace handler must
    verify the correctness itself.
    """

    def __init__(self, message):
        self.message = message
        self.line_number = None


    def __str__(self):
        if self.line_number is not None:
            return '%s, line %s' % (self.message, self.line_number)
        return self.message
