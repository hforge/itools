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
import Index
import Lucene
import Segment




class Document(Text.Text):
    def _load(self):
        data = self.resource.get_data()
        lines = data.split('\n')
        self.title = lines[0]
        self.body = '\n'.join(lines[3:])

# Create and get a new empty index
index = Index.Index(fields=[('title', True, True), ('body', True, False)])
tests = get_handler('tests')
if tests.has_resource('index'):
    tests.del_resource('index')
tests.set_handler('index', index)
index_resource = tests.get_resource('index')
index = Index.Index(index_resource)

resource_names = [ x for x in tests.get_resources() if x.endswith('.txt') ]
resource_names.sort()
documents = [ Document(tests.get_resource(x)) for x in resource_names ]


def profile_indexing():
    for document in documents:
        index.index_document(document)


def profile_search():
    for word in ('forget', 'lion', 'hit'):
        index.search(body=word)


if __name__ == '__main__':
    profile.run('profile_indexing()')
##    print
##    print
##    print
##    profile.run('profile_search()')

