#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2007 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
isetup-quality.py is a small tool to do some measurements on Python files
"""

# Import from the Standard Library
from optparse import OptionParser
from subprocess import call
from tempfile import TemporaryFile
from token import tok_name
from tokenize import generate_tokens, TokenError

# Import from itools
import itools
from itools import git

# Global variables
worse = -1


def analyse_file_pass1(filename):
    """This function analyses a file and produces a dict with these members:
     - 'lines': number of lines;
     - 'bad_length': number of lines longer than 79 characters;
     - 'bad_end': number of lines with trailing whitespaces;
     - 'tabs': number of lines with tabulators;
    """
    stats = {
        'lines': 0,
        'bad_length': 0,
        'bad_end': 0,
        'tabs': 0}

    for line in file(filename):
        # Number of line
        stats['lines'] += 1

        # Bad length
        if len(line) > 79:
            stats['bad_length'] += 1

        # Bad end
        if len(line.rstrip()) != len(line.rstrip('\n\x0b\x0c\r')):
            stats['bad_end'] += 1

        # Tabs ?
        if '\t' in line:
            stats['tabs'] += 1

    return stats


def analyse_file_pass2(filename):
    """This function analyses a file and produces a dict with these members:
     - 'tokens': number of tokens;
     - 'string_exception': number of lines with string exceptions;
     - 'except_all': number of line where all exceptions are catched;
     - 'bad_indentation': number of lines with a bad indentation;
     - 'syntax_error': number of lines with an error;
    """
    stats = {
        'tokens': 0,
        'string_exception': 0,
        'except_all': 0,
        'bad_indentation': 0,
        'bad_import': 0,
        'syntax_error': 0}
    try:
        tokens = generate_tokens(file(filename).readline)

        last_name = ''
        current_line = 0
        current_indentation = 0

        header = True
        command_on_line = False
        import_on_line = False

        for tok_type, value, begin, _, _ in tokens:
            # Tokens number
            stats['tokens'] += 1

            # Find the line number
            if begin[0] > current_line:
                current_line = begin[0]

            # Find NEWLINE
            if tok_name[tok_type] == 'NEWLINE':
                if command_on_line and not import_on_line:
                    header = False
                command_on_line = False
                import_on_line = False


            # Find command
            if tok_name[tok_type] not in [
                'COMMENT', 'STRING', 'NEWLINE', 'NL']:
                command_on_line = True
            # Find import and test
            if tok_name[tok_type] == 'NAME' and value == 'import':
                import_on_line = True
                if not header:
                    stats['bad_import'] += 1

            # Indentation management
            if tok_name[tok_type] == 'INDENT':
                if '\t' in value or len(value) - current_indentation != 4:
                    stats['bad_indentation'] += 1
                current_indentation = len(value)
            if tok_name[tok_type] == 'DEDENT':
                current_indentation = begin[1]

            # String exceptions except or raise ?
            if ((last_name == 'except' or last_name == 'raise') and 
                tok_name[tok_type] == 'STRING'):
                stats['string_exception'] += 1

            # except: ?
            if (last_name == 'except' and tok_name[tok_type] == 'OP' and
                value == ':'):
                stats['except_all'] += 1

            # Last_name
            if tok_name[tok_type] == 'NAME':
                last_name = value
            else:
                last_name = ''

    except (TokenError, IndentationError):
        stats['syntax_error'] = 1

    return stats


def analyse_file(filename):
    """This function merges the two dictionnaries for a file
    """
    stats = {}

    stats1 = analyse_file_pass1(filename)
    for key, value in stats1.iteritems():
        stats[key] = value

    stats2 = analyse_file_pass2(filename)
    for key, value in stats2.iteritems():
        stats[key] = value

    return stats


def print_list(title, string_list):
    if len(string_list) != 0:
        print title
        print '-'*len(title)
        for line in string_list:
            print line
        print


def print_worses(db, criteria):
    sort_key = lambda x: sum([ x[c] for c in criteria ])
    if worse >= 0:
        db.sort(key=sort_key, reverse=True)

        if worse != 0:
            number = worse
        else:
            number = None

        first = True
        for f in db[:number]:
            if sort_key(f) != 0:
                if first:
                    print 'Worse files:'
                    first = False
                print '- %s (%d)' % (f['filename'], sort_key(f))
        if not first:
            print

    
def analyse(filenames):
    """Analyse a list of files
    """
    stats = {
        'lines': 0,
        'bad_length': 0,
        'bad_end': 0,
        'tabs': 0,
        'tokens': 0,
        'string_exception': 0,
        'except_all': 0,
        'bad_indentation':0,
        'bad_import': 0,
        'syntax_error': 0}

    files_db = []
    for filename in filenames:
        f_stats = analyse_file(filename)
        if f_stats['lines'] != 0:
            for key, value in f_stats.iteritems():
                stats[key] += value
            f_stats['filename'] = filename
            files_db.append(f_stats)

    # Show quality summary
    print
    print 'Code length: %d lines, %d tokens' % (stats['lines'],
                                                stats['tokens'])
    print

    # Aesthetics (and readibility)
    comments = [
        ('with tabulators', stats['tabs']),
        ('bad indented', stats['bad_indentation']),
        ('longer than 79 characters', stats['bad_length']),
        ('with trailing whitespaces', stats['bad_end'])]
    show_comments = [
        '%5.02f%% lines ' % ((value*100.0)/stats['lines']) + comment
        for comment, value in comments if value != 0 ]
    print_list('Aesthetics (and readibility)', show_comments)
    print_worses(files_db, ['tabs', 'bad_indentation', 'bad_length',
                            'bad_end'])

    # Exception handling
    comments = [
        ('string exceptions are used', stats['string_exception']),
        ('all exceptions are catched', stats['except_all'])]
    show_comments = []
    for c in comments:
        if c[1] != 0:
            show_comments.append('%d times ' % c[1] + c[0])
    print_list('Exception handling', show_comments)
    print_worses(files_db, ['string_exception', 'except_all'])

    # Imports
    if stats['bad_import'] != 0:
        show_comments = ['%d misplaced imports' % stats['bad_import']]
    else:
        show_comments = []
    print_list('Imports', show_comments)
    print_worses(files_db, ['bad_import'])
 

def fix(filenames):
    for filename in filenames:
        lines = [ x.rstrip() + '\n' for x in open(filename).readlines() ]
        open(filename, 'w').write(''.join(lines))


if __name__ == '__main__':
    # The command line parser
    usage = '%prog [OPTIONS] [FILES]'
    version = 'itools %s' % itools.__version__
    description = (
        'Shows some statistics about the quality of the Python code.')
    parser = OptionParser(usage, version=version, description=description)

    parser.add_option(
        '-f', '--fix', action='store_true', dest='fix',
        help="makes some small improvements to the source code "
             "(MAKE A BACKUP FIRST)")

    parser.add_option(
        '-w', '--worse',
        action='store', type='int', dest='worse',
        help='number of worse files showed, 0 for all')
    parser.set_defaults(worse=-1)

    options, args = parser.parse_args()
    worse = options.worse

    # Making of filenames
    if args:
        filenames = args
    elif git.is_available():
        filenames = git.get_filenames()
        filenames = [ x for x in filenames if x.endswith('.py') ]
    else:
        tmp = TemporaryFile()
        call(['find', '-name', '*.py'], stdout=tmp)
        tmp.seek(0)
        filenames = [ x.strip() for x in tmp.readlines() ]
        tmp.close()

    # Analyse
    analyse(filenames)

    # Fix
    if options.fix is True:
        print 'FIXING...'
        fix(filenames)
        print 'DONE'
        analyse(filenames)
