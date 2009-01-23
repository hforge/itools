# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
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

"""
To build a query:

  from itools.xapian import PhraseQuery, AndQuery
  s1 = PhraseQuery('format', 'Actu')
  s2 = PhraseQuery('archive', True)
  s3 = PhraseQuery('workflow_state', 'public')
  query = AndQuery(s1, s2, s3)
"""



class BaseQuery(object):

    def __repr__(self):
        return "<%s.%s(%s)>" % (
            self.__module__,
            self.__class__.__name__,
            self.__repr_parameters__())



class AllQuery(BaseQuery):

    def __repr_parameters__(self):
        return ''



class RangeQuery(BaseQuery):

    def __init__(self, name, left, right):
        self.name = name
        self.left = left
        self.right = right


    def __repr_parameters__(self):
        return "%r, %r, %r" % (self.name, self.left, self.right)



class PhraseQuery(BaseQuery):

    def __init__(self, name, value):
        self.name = name
        self.value = value


    def __repr_parameters__(self):
        return "%r, %r" % (self.name, self.value)


############################################################################
# Boolean or complex searches
############################################################################
class AndQuery(BaseQuery):

    def __init__(self, *args):
        self.atoms = [ x for x in args if not isinstance(x, AllQuery) ]
        if len(self.atoms) == 0 and len(args) > 0:
            self.atoms = [AllQuery()]


    def __repr_parameters__(self):
        return ', '.join([ repr(x) for x in self.atoms ])



class OrQuery(BaseQuery):

    def __init__(self, *args):
        for x in args:
            if isinstance(x, AllQuery):
                self.atoms = [x]
                break
        else:
            self.atoms = args


    def __repr_parameters__(self):
        return ', '.join([ repr(x) for x in self.atoms ])



class NotQuery(BaseQuery):

    def __init__(self, query):
        self.query = query



class StartQuery(BaseQuery):

    def __init__(self, name, value):
        self.name = name
        self.value = value


    def __repr_parameters__(self):
        return "%r, %r" % (self.name, self.value)
