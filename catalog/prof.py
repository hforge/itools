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


# Import from Python
import profile

# Import from itools
from itools.handlers import get_handler, Text
from itools.catalog.Catalog import Catalog




class Document(Text.Text):
    def _load(self):
        # Pre-process (load as unicode)
        Text.Text._load(self)
        data = self._data
        del self._data
        # Extract the title and body
        lines = data.split('\n')
        self.title = lines[0]
        self.body = '\n'.join(lines[3:])


# Create and get a new empty index
catalog = Catalog(fields=[('title', 'text', True, True),
                          ('body', 'text', True, False)])
tests = get_handler('tests')
if tests.has_resource('catalog'):
    tests.del_resource('catalog')
tests.set_handler('catalog', catalog)
catalog_resource = tests.get_resource('catalog')
catalog = Catalog(catalog_resource)

resource_names = [ x for x in tests.get_resources() if x.endswith('.txt') ]
resource_names.sort()
documents = [ Document(tests.get_resource(x)) for x in resource_names ]


def profile_indexing():
    for document in documents:
        catalog.index_document(document)


def profile_search():
    for word in ('forget', 'lion', 'hit'):
        catalog.search(body=word)


if __name__ == '__main__':
    profile.run('profile_indexing()')
##    print
##    print
##    print
##    profile.run('profile_search()')

