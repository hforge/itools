#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2009 David Versmisse <david.versmisse@itaapy.com>
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

# Import from the standard library
from marshal import loads
from optparse import OptionParser
from re import compile
from sys import exit

# Import from xapian
from xapian import Database, DatabaseOpeningError, Enquire, Query

# Import from itools
from itools import __version__


def get_db(path):
    # Get the DB
    try:
        return Database(path)
    except DatabaseOpeningError:
        print 'Bad DB, sorry'
        exit(1)


def get_metadata(db):
    metadata = db.get_metadata('metadata')
    if metadata == '':
        return {}
    else:
        return loads(metadata)


def get_docs(db):
    enquire = Enquire(db)
    enquire.set_query(Query(''))
    docs_max = enquire.get_mset(0,0).get_matches_upper_bound()
    return [doc.get_document() for doc in  enquire.get_mset(0, docs_max)]


def get_regexp(regexp):
    if regexp is not None:
        try:
            return compile(regexp)
        except Exception, error:
            print 'Your regexp "%s" is invalid: %s' % (regexp, str(error))
            exit(1)
    return None


def dump_summary(db, metadata):
    print 'Summary'
    print '======='
    print
    print (' * You have %d document(s) stocked in your '
           'database. ') % db.get_doccount()

    total = stored = indexed = 0
    key_field = None
    for name, info in metadata.iteritems():
        total += 1
        if 'key_field' in info:
            key_field = name
        if 'value' in info:
            stored += 1
        if 'prefix' in info:
            indexed += 1
    print ' * %d field(s) (%d stored, %d indexed).' % (total, stored, indexed)
    if key_field is not None:
        print ' * key field: "%s"' % key_field


def dump_fields(db, metadata, docs, only_field, show_values, show_terms):
    print 'FIELDS'
    print '======'
    print

    for name, info in metadata.iteritems():
        if only_field is not None and not only_field.match(name):
            continue

        print name
        print '-'*len(name)

        # Info
        if 'key_field' in info:
            print ' * key field'
        if 'value' in info:
            print ' * stored'
        else:
            print ' * not stored'
        if 'prefix' in info:
            print ' * indexed'
        else:
            print ' * not indexed'

        # Values
        if 'value' in info and show_values:
            value = info['value']
            print ' * raw values:'
            for doc in docs:
                print '   "%s"' % doc.get_value(value)

        # Terms
        if 'prefix' in info and show_terms:
            prefix = info['prefix']
            prefix_size = len(prefix)
            terms = set([ t.term[prefix_size:]
                          for t in db.allterms(prefix) ])
            print ' * raw terms:'
            for term in terms:
                print '   "%s"' % term

        print


def dump_docs(db, metadata, docs, only_doc, only_field, show_values,
              show_terms):
    print 'DOCUMENTS'
    print '========='
    print

    # Prepare the good docs
    if only_doc is not None:
        show_docs = []
        for doc in docs:
            for info in metadata.itervalues():
                if 'value' in info:
                    value = doc.get_value(info['value'])
                    if only_doc.match(value):
                        show_docs.append(doc)
    else:
        show_docs = docs

    # Show the documents
    for doc in show_docs:
        title = 'document id#%d' % doc.get_docid()
        print title
        print '-'*len(title)

        terms = [term.term for term in doc]
        for name, info in metadata.iteritems():
            if only_field is not None and not only_field.match(name):
                continue

            if show_values or show_terms:
                print ' * %s:' % name

            # Value
            if 'value' in info and show_values:
                print '   - raw value: "%s"' % doc.get_value(info['value'])

            # Terms
            if 'prefix' in info and show_terms:
                prefix = info['prefix']
                prefix_size = len(prefix)
                print '   - raw terms:'
                for term in terms:
                    if term.startswith(prefix):
                        print '     "%s"' % term[prefix_size:]
        print



if  __name__ == '__main__':
    # Options initialisation
    usage = '%prog [options] <path to catalog>'
    description = 'Inspect an itools.xapian catalog '
    parser = OptionParser(usage, version=__version__, description=description)

    # Dump the values
    parser.add_option('-v', '--values', action='store_true', dest='values',
                      help='show all values stocked for a field',
                      default=False)

    # Dump the terms
    parser.add_option('-t', '--terms', action='store_true', dest='terms',
                      help='show all terms stocked for a field',
                      default=False)

    # Dump all fields
    parser.add_option('-f', '--fields', action='store_true', dest='fields',
                      help='dump all the fields stored in the database')

    # Dump all docs
    parser.add_option('-d', '--docs', action='store_true', dest='docs',
                      help='dump all documents stored in the database')

    # Only field
    parser.add_option('--only_field', action='store', dest='only_field',
                      metavar='REGEXP',
                      help='dump only fields that match the given regexp')

    # Only Docs
    parser.add_option('--only_doc', action='store', dest='only_doc',
                      metavar='REGEXP',
                      help='dump only documents that have at least a "value" '
                           'that matches the regular expression')

    # Parse !
    opts, args = parser.parse_args()

    # Configuration file
    if len(args) != 1:
        parser.print_help()
        exit(1)
    db_path = args[0]


    # GO GO GO

    # Inspect the db
    db = get_db(db_path)
    metadata = get_metadata(db)
    docs = get_docs(db)

    # Compile the regexp
    only_field = get_regexp(opts.only_field)
    only_doc = get_regexp(opts.only_doc)

    # No field, No doc => just a summary
    if not (opts.fields or opts.docs):
        dump_summary(db, metadata)
    if opts.fields:
        dump_fields(db, metadata, docs, only_field, opts.values, opts.terms)
    if opts.docs:
        dump_docs(db, metadata, docs, only_doc, only_field, opts.values,
                  opts.terms)





