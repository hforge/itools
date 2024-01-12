# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2008, 2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2008 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2008, 2011 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2008-2010 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2011 Nicolas Deram <nderam@gmail.com>
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

  from itools.database import PhraseQuery, AndQuery
  s1 = PhraseQuery('format', 'Actu')
  s2 = PhraseQuery('archive', True)
  s3 = PhraseQuery('workflow_state', 'public')
  query = AndQuery(s1, s2, s3)
"""

# Import from the Standard Library
from pprint import PrettyPrinter, _recursion


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
        return f"{self.name!r}, {self.left!r}, {self.right!r}"



class PhraseQuery(BaseQuery):

    def __init__(self, name, value):
        self.name = name
        self.value = value


    def __repr_parameters__(self):
        return f"{self.name!r}, {self.value!r}"


############################################################################
# Boolean or complex searches
############################################################################
class _MultipleQuery(BaseQuery):

    def __init__(self, *args):
        self.atoms = []
        for arg in args:
            self.append(arg)


    def __repr_parameters__(self):
        return '\n' + ',\n'.join([ repr(x) for x in self.atoms ])


    def append(self, atom):
        raise NotImplementedError


class _AndQuery(_MultipleQuery):

    def append(self, atom):
        atoms = self.atoms
        n = len(atoms)
        if n == 0:
            atoms.append(atom)
        elif n == 1 and type(atoms[0]) is AllQuery:
            self.atoms = [atom]
        elif type(atom) is not AllQuery:
            atoms.append(atom)


class _OrQuery(_MultipleQuery):

    def append(self, atom):
        atoms = self.atoms
        n = len(atoms)
        if n == 0:
            atoms.append(atom)
        elif type(atoms[0]) is AllQuery:
            pass
        elif type(atom) is AllQuery:
            self.atoms = [atom]
        else:
            atoms.append(atom)


def _flat_query(cls, *args):
    query = cls()
    for subquery in args:
        if isinstance(subquery, cls):
            for atom in subquery.atoms:
                query.append(atom)
        else:
            query.append(subquery)
    return query


def AndQuery(*args):
    return _flat_query(_AndQuery, *args)


def OrQuery(*args):
    return _flat_query(_OrQuery, *args)


class NotQuery(BaseQuery):

    def __init__(self, query):
        self.query = query

    def __repr_parameters__(self):
        return repr(self.query)


class StartQuery(BaseQuery):

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr_parameters__(self):
        return f"{self.name!r}, {self.value!r}"


class TextQuery(BaseQuery):

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr_parameters__(self):
        return f"{self.name!r}, {self.value!r}"


class QueryPrinter(PrettyPrinter):

    def _format(self, query, stream, indent, allowance, context, level):
        level = level + 1
        objid = id(query)
        if objid in context:
            stream.write(_recursion(query))
            self._recursive = True
            self._readable = False
            return
        rep = self._repr(query, context, level - 1)
        typ = type(query)
        sepLines = len(rep) > (self._width - 1 - indent - allowance)
        write = stream.write

        if self._depth and level > self._depth:
            write(rep)
            return

        if issubclass(typ, (_AndQuery, _OrQuery, NotQuery)):
            write(f'<{query.__module__}.{query.__class__.__name__}(')
            if self._indent_per_level > 1:
                write((self._indent_per_level - 1) * ' ')
            if issubclass(typ, NotQuery):
                atoms = [query.query]
            else:
                atoms = query.atoms
            if atoms:
                context[objid] = 1
                indent = indent + self._indent_per_level
                for atom in atoms:
                    if sepLines:
                        write(f"\n{' ' * indent}")
                    self._format(atom, stream, indent + 2,
                            allowance + 1, context, level)
                indent = indent - self._indent_per_level
                del context[objid]
            write('>')
            return

        write(rep)


def pprint_query(query, stream=None, indent=1, width=80, depth=None):
    printer = QueryPrinter(stream=stream, indent=indent, width=width,
            depth=depth)
    printer.pprint(query)
