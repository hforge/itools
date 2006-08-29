# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the future
from __future__ import with_statement

# Import from the Standard Library
from os import getpid
import profile
import sys
from time import time

# Import from itools
from itools import vfs
from itools.handlers import Text
from itools.xml import XML
from itools.html import HTML
from itools.catalog.catalog import Catalog


def vmsize(scale={'kB': 1024.0, 'mB': 1024.0*1024.0,
                  'KB': 1024.0, 'MB': 1024.0*1024.0}):
    with open('/proc/%d/status' % getpid()) as file:
        v = file.read()
    i = v.index('VmSize:')
    v = v[i:].split(None, 3)  # whitespace
    # convert Vm value to bytes
    return float(v[1]) * scale[v[2]]



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


def load_catalog():
    global catalog
    catalog = Catalog('/tmp/catalog_prof')


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


def index_documents():
    for document in documents:
        catalog.index_document(document)
    catalog.save_state()


def search_documents():
    for word in ('forget', 'lion', 'hit'):
        catalog.search(body=word)


if __name__ == '__main__':
    # Check input
    options = ('bench-index', 'bench-search',
               'bench-memory',
               'profile-index', 'profile-search')
    usage = "This script expects one of the following options:\n\n"
    for option in options:
        usage += '    %s\n' % option

    if len(sys.argv) != 2:
        print usage
        sys.exit()

    option = sys.argv[1]
    if option not in options:
        print usage
        sys.exit()

    # Proceed
    if option == 'profile-index':
        create_catalog()
        load_documents()
        profile.run('index_documents()')
    elif option == 'profile-search':
        load_catalog()
        profile.run('search_documents()')
    elif option == 'bench-index':
        create_catalog()
        load_documents()
        t0 = time()
        index_documents()
        print time() - t0
    elif option == 'bench-search':
        load_catalog()
        t0 = time()
        search_documents()
        print time() - t0
    elif option == 'bench-memory':
        load_catalog()
        index = catalog.get_index('body')
        tree_file = vfs.open(index.uri.resolve2('tree'))
        m0 = vmsize()
        try:
            index._index.root._load_children_deep(tree_file)
        finally:
            tree_file.close()
        m1 = vmsize()
        print '%s - %s = %s' % (m1, m0, m1-m0)
