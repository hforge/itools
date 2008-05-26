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
from glob import glob
from optparse import OptionParser
from subprocess import call
from tempfile import TemporaryFile
from token import tok_name
from tokenize import generate_tokens, TokenError
from types import ListType

# Import from itools
import itools
from itools import git, vfs


problems = {'tabs': u'with tabulators',
            'bad_indentation': u'bad indented',
            'bad_length': u'longer than 79 characters',
            'bad_end' : u'with trailing whitespaces',
            'string_exception': u'string exceptions are used',
            'except_all': u'all exceptions are catched'}


def analyse_file_pass1(filename):
    """This function analyses a file and produces a dict with these members:
     - 'lines': number of lines;
     - 'bad_length': list of lines longer than 79 characters;
     - 'bad_end': list of lines with trailing whitespaces;
     - 'tabs': list of lines with tabulators;
    """

    stats = {'bad_length': [], 'bad_end': [], 'tabs': []}

    current_line = -1
    for current_line, line in enumerate(file(filename)):
        # Bad length
        if len(line) > 79:
            stats['bad_length'].append(current_line+1)

        # Bad end
        if len(line.rstrip()) != len(line.rstrip('\n\x0b\x0c\r')):
            stats['bad_end'].append(current_line+1)

        # Tabs ?
        if '\t' in line:
            stats['tabs'].append(current_line+1)

    stats['lines'] = current_line+1

    return stats


def analyse_file_pass2(filename):
    """This function analyses a file and produces a dict with these members:
     - 'tokens': number of tokens;
     - 'string_exception': list of lines with string exceptions;
     - 'except_all': list of line where all exceptions are catched;
     - 'bad_indentation': list of lines with a bad indentation;
     - 'syntax_error': list of lines with an error;
    """
    stats = {
        'tokens': 0,
        'string_exception': [],
        'except_all': [],
        'bad_indentation': [],
        'bad_import': [],
        'syntax_error': []}
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
            if tok_name[tok_type] not in ['COMMENT', 'STRING', 'NEWLINE',
                                          'NL']:
                command_on_line = True

            # Find import and test
            if tok_name[tok_type] == 'NAME' and value == 'import':
                import_on_line = True
                if not header:
                    stats['bad_import'].append(current_line)

            # Indentation management
            if tok_name[tok_type] == 'INDENT':
                if '\t' in value or len(value) - current_indentation != 4:
                    stats['bad_indentation'].append(current_line)
                current_indentation = len(value)
            if tok_name[tok_type] == 'DEDENT':
                current_indentation = begin[1]

            # String exceptions except or raise ?
            if ((last_name == 'except' or last_name == 'raise') and
                tok_name[tok_type] == 'STRING'):
                stats['string_exception'].append(current_line)

            # except: ?
            if (last_name == 'except' and tok_name[tok_type] == 'OP' and
                value == ':'):
                stats['except_all'].append(current_line)

            # Last_name
            if tok_name[tok_type] == 'NAME':
                last_name = value
            else:
                last_name = ''

    # Syntax error ?
    except (TokenError, IndentationError):
        stats['syntax_error'].append(current_line)

    return stats


def analyse_file(filename):
    """This function merges the two dictionaries for a file
    """
    stats = analyse_file_pass1(filename)
    for key, value in analyse_file_pass2(filename).iteritems():
        stats[key] = value

    return stats


def print_list(title, string_list):
    if len(string_list) != 0:
        print title
        print '-'*len(title)
        for line in string_list:
            print line
        print


def print_worses(db, worse, criteria):
    if worse >= 0:
        sort_key = lambda f: sum([ len(f[c]) for c in criteria ])

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


def analyse(filenames, worse, show_lines):
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
                if type(value) == ListType:
                    stats[key] += len(value)
                else:
                    stats[key] += value
            f_stats['filename'] = filename
            files_db.append(f_stats)

    # Show quality summary
    print
    print 'Code length: %d lines, %d tokens' % (stats['lines'],
                                                stats['tokens'])
    print

    # Show number lines
    if show_lines:
        comments = []
        infos = files_db[0]
        for problem in problems.keys():
            lines = infos[problem]
            if lines:
                comments.append('Lines %s:\n' % problems[problem])
                for line in lines:
                    comments.append('%s +%d' % (filename, line))
                comments.append('\n')
        if comments:
            print '\n'.join(comments)
        else:
            print u'This file is perfect !'
        return

    # Aesthetics (and readibility)
    show_comments = []
    aesthetics_problems = ['tabs', 'bad_indentation', 'bad_length', 'bad_end']
    for problem in aesthetics_problems:
        stat = stats[problem]
        if stat != 0:
            pourcent = (stats[problem] * 100.0)/stats['lines']
            show_comments.append('%5.02f%% lines %s' % (pourcent,
                                                        problems[problem]))
    print_list('Aesthetics (and readibility)', show_comments)
    print_worses(files_db, worse, aesthetics_problems)

    # Exception handling
    show_comments = []
    exception_problems = ['string_exception', 'except_all']
    for problem in exception_problems:
        stat = stats[problem]
        if stat != 0:
            show_comments.append('%d times %s' % (stat, problems[problem]))
    print_list('Exception handling', show_comments)
    print_worses(files_db, worse, exception_problems)

    # Imports
    if stats['bad_import'] != 0:
        show_comments = ['%d misplaced imports' % stats['bad_import']]
    else:
        show_comments = []
    print_list('Imports', show_comments)
    print_worses(files_db, worse, ['bad_import'])


def fix(filenames):
    for filename in filenames:
        lines = []
        for line in open(filename).readlines():
            # Calculate the indentation level
            # http://docs.python.org/ref/indentation.html
            indent = 0
            for c in line:
                if c == ' ':
                    indent += 1
                elif c == '\t':
                    indent = ((indent/8) + 1) * 8
                else:
                    break
            # Remove trailing spaces & remove tabulators used for indentation
            line = ' ' * indent + line.strip() + '\n'
            # Append
            lines.append(line)

        # Save
        open(filename, 'w').write(''.join(lines))


if __name__ == '__main__':
    # The parser
    usage = '%prog [OPTIONS] [FILES]'
    version = 'itools %s' % itools.__version__
    description = 'Shows some statistics about the quality of the Python code'
    parser = OptionParser(usage, version=version, description=description)

    # Fix
    parser.add_option('-f', '--fix', action='store_true', dest='fix',
                      default=False, help='makes some small improvements to '
                      ' the source code (MAKE A BACKUP FIRST)')

    # Worse
    parser.add_option('-w', '--worse', action='store', type='int',
                      metavar='INT', dest='worse', default=-1,
                      help='number of worse files showed, 0 for all')

    # Show lines
    parser.add_option('-s', '--show-lines', action='store_true',
                      dest='show_lines', default=False,
                      help='give the line of each problem found')

    options, args = parser.parse_args()

    # Filenames
    if args:
        filenames = set([])
        for arg in args:
            filenames = filenames.union(glob(arg))
        filenames = list(filenames)
    elif git.is_available():
        filenames = git.get_filenames()
        filenames = [ x for x in filenames if x.endswith('.py') ]
    else:
        filenames = []
        here = vfs.open('.')
        for uri in vfs.traverse('.'):
            if vfs.is_file(uri) and uri.path.get_name().endswith('.py'):
                filenames.append(str(here.uri.path.get_pathto(uri.path)))

    # Check options
    if len(filenames)==0:
        parser.error(u'Please give at least one file to analyse.')
    if options.worse>0 and options.show_lines==True:
        parser.error(u'Options --worse and --show-lines are mutually exclusive.')

    # Analyse
    analyse(filenames, options.worse, options.show_lines)

    # Fix
    if options.fix is True:
        print 'FIXING...'
        fix(filenames)
        print 'DONE'
        analyse(filenames, options.worse, options.show_lines)
