# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
To build a query:

  from itools.catalog import Query
  s1 = Query.Simple('format', 'Actu')
  s2 = Query.Simple('archive', True)
  c1 = Query.Complex(s1, 'and', s2)
  s3 = Query.Simple('workflow_state', 'public')
  query = Query.Complex(c1, 'and', s3)
"""


class Simple(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class Complex(object):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
