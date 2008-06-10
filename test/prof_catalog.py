# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
import profile
import sys
from time import time

# Import from itools
from itools import vfs
from itools.xml import get_element, TEXT
from itools.html import HTMLFile
from itools.xapian import Catalog, make_catalog, CatalogAware, TextField



docs_path = '/usr/share/doc/python-docs-2.5.1/html/lib'


class Document(CatalogAware, HTMLFile):

    def get_catalog_fields(self):
        return [TextField('title', is_stored=True), TextField('body')]


    def get_catalog_values(self):
        values = {}
        values['title'] = self.title()
        values['body'] = self.body()
        return values


    def title(self):
        title = get_element(self.events, 'title')
        return title.get_content()


    def body(self):
        text = [ unicode(value, 'latin-1')
                 for event, value, line in self.events
                 if event == TEXT ]
        return u' '.join(text)
        # FIXME Should be...
##        return self.to_text(encoding=)



def create_catalog():
    print 'Creating catalog...',
    global catalog

    if vfs.exists('/tmp/catalog_prof'):
        vfs.remove('/tmp/catalog_prof')
    # Create and get a new empty catalog
    catalog = make_catalog('/tmp/catalog_prof')
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
            doc.load_state()
        except:
            print doc_uri, '!!'
        else:
            documents.append(doc)
    print 'done'


def index_documents():
    for document in documents:
        catalog.index_document(document)
    catalog.save_changes()


def search_documents():
    for word in ('forget', 'lion', 'hit'):
        catalog.search(body=word)


if __name__ == '__main__':
    # Check input
    options = ('bench-index', 'bench-search',
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
