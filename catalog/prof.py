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
from time import time

# Import from itools
from itools.handlers import get_handler, Text
from itools.resources import get_resource
from itools.xml import HTML
from itools.catalog.Catalog import Catalog



docs_path = '/usr/share/doc/python-docs-2.3.4/html/lib'


class Document(HTML.Document):
    def title(self):
        head = self.get_head()
        return unicode(head.get_elements('title')[0].children)


    def body(self):
        return unicode(self.get_body().children)



def create_catalog():
    print 'Creating catalog...',
    global catalog
    # Create and get a new empty index
    catalog = Catalog(fields=[('title', 'text', True, True),
                              ('body', 'text', True, False)])
    tests = get_handler('tests')
    if tests.has_resource('catalog'):
        tests.del_resource('catalog')
    tests.set_handler('catalog', catalog)
    catalog_resource = tests.get_resource('catalog')
    catalog = Catalog(catalog_resource)
    print 'done'


documents = []
def load_documents():
    print 'Loading documents...',
    src = get_resource(docs_path)
    resource_names = [ x for x in src.get_resources() if x.endswith('.html') ]
    resource_names.sort()
    for name in resource_names[:120]:
        try:
            doc = Document(src.get_resource(name))
        except:
            pass
        else:
            documents.append(doc)
    print 'done'


##catalog = Catalog(fields=[('title', 'text', True, True),
##                          ('body', 'text', True, False)])


def profile_indexing():
    for document in documents[:50]:
        catalog.index_document(document)
    catalog.save()


def profile_search():
    for word in ('forget', 'lion', 'hit'):
        catalog.search(body=word)


if __name__ == '__main__':
    create_catalog()
    load_documents()
    # Benchmark
    t0 = time()
    profile_indexing()
    t1 = time()
    print t1 - t0
    # Profile
##    profile.run('profile_indexing()')

##    print
##    print
##    print
##    profile.run('profile_search()')

