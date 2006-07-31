# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
import profile
import sys
from time import time

# Import from itools
from itools import vfs
from itools.handlers import Text
from itools.xml import XML
from itools.html import HTML
from itools.catalog.catalog import Catalog



docs_path = '/usr/share/doc/python-docs-2.4.3/html/lib'


class Document(HTML.Document):

    def title(self):
        head = self.get_head()
        title = head.get_elements('title')[0]
        return title.get_content()


    def body(self):
        return self.to_text()



def create_catalog():
    print 'Creating catalog...',
    global catalog
    # Create and get a new empty index
    catalog = Catalog(fields=[('title', 'text', True, True),
                              ('body', 'text', True, False)])
    if vfs.exists('/tmp/catalog_prof'):
        vfs.remove('/tmp/catalog_prof')
    catalog.save_state_to('/tmp/catalog_prof')
    catalog = Catalog('/tmp/catalog_prof')
    print 'done'


documents = []
def load_documents():
    print 'Loading documents...',
    src = vfs.open(docs_path)
    resource_names = [ x for x in src.get_names() if x.endswith('.html') ]
    resource_names.sort()
    for name in resource_names:
        doc_uri = src.uri.resolve2(name)
        doc = Document(doc_uri)
        try:
            doc = {'title': doc.title(), 'body': doc.body()}
        except:
            print doc_uri, '!!'
        else:
            documents.append(doc)
    print 'done'


##catalog = Catalog(fields=[('title', 'text', True, True),
##                          ('body', 'text', True, False)])


def profile_indexing():
    for document in documents:
        catalog.index_document(document)
    catalog.save_state()


def profile_search():
    for word in ('forget', 'lion', 'hit'):
        catalog.search(body=word)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        option = sys.argv[1]
    else:
        option = None

    if option == 'profile':
        create_catalog()
        load_documents()
        # Profile
        profile.run('profile_indexing()')
##        print
##        profile.run('profile_search()')
    elif option == 'bench':
        create_catalog()
        load_documents()
        # Benchmark
        t0 = time()
        profile_indexing()
        t1 = time()
        print t1 - t0
    else:
        print "This script expects only one of the two options: 'profile'" \
              " or 'bench'."
