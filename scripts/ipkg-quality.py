# Copyright (C) 2007 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2007-2009, 2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@supinfo.com>
# Copyright (C) 2008 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2008-2009 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@oursours.net>
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
ipkg-quality.py is a small tool to do some measurements on Python files
"""

from glob import glob
from optparse import OptionParser
from os.path import basename, relpath
from tokenize import generate_tokens, TokenError, DEDENT, INDENT
import ast

# Import from itools
import itools
from itools.core import merge_dicts
from itools.fs import lfs
from itools.pkg import open_worktree


# Define list of problems
code_length = {
    'title': 'Code length',
    'keys': {'lines': 'Number of lines', 'tokens': 'Number of tokens'},
    'pourcent': False}

aesthetics_problems = {
     'title': 'Style',
     'keys': {'tabs':  'with tabulators',
              'bad_indentation': 'bad indented',
              'bad_length': 'longer than 79 characters',
              'bad_end': 'with trailing whitespaces'},
     'pourcent': True}

exception_problems = {
    'title': 'Exception handling',
    'keys': {
        'string_exception': 'string exceptions are used',
        'except_all': 'all exceptions are catched'},
    'pourcent': False}

import_problems = {
    'title': 'Import problems',
    'keys': {'bad_import': 'misplaced imports'},
    'pourcent': False}

problems = merge_dicts(
    aesthetics_problems['keys'],
    exception_problems['keys'],
    import_problems['keys'])


###########################################################################
# Plugins (by line)
###########################################################################

class LineLengthPlugin(object):
    key = 'bad_length'

    @classmethod
    def analyse_line(self, line):
        # FIXME 80 is good for '\n' or '\r' ended files, not for '\r\n'
        return len(line) > 80


class TrailingSpacePlugin(object):
    key = 'bad_end'

    @classmethod
    def analyse_line(self, line):
        return len(line.rstrip()) != len(line.rstrip('\n\x0b\x0c\r'))


class TabsPlugin(object):
    key = 'tabs'

    @classmethod
    def analyse_line(self, line):
        return '\t' in line


line_plugins = [LineLengthPlugin, TrailingSpacePlugin, TabsPlugin]


###########################################################################
# Plugins (by tokens)
###########################################################################

class IndentPlugin(object):
    key = 'bad_indentation'

    def __init__(self):
        self.current_indentation = 0


    def analyse_token(self, token, value, srow, scol):
        indent = self.current_indentation
        # Indentation management
        if token == INDENT:
            self.current_indentation = len(value)
            return '\t' in value or len(value) - indent != 4
        elif token == DEDENT:
            self.current_indentation = scol
        return False


token_plugins = [IndentPlugin]



###########################################################################
# Plugins (by AST)
###########################################################################

class ExceptAllPlugin(object):
    key = 'except_all'

    @classmethod
    def analyse_node(cls, node):
        return type(node) is ast.ExceptHandler and node.type is None


class StringException(object):
    key = 'string_exception'

    @classmethod
    def analyse_node(cls, node):
        node_type = type(node)
        # except <str>:
        if node_type is ast.ExceptHandler:
            # TODO except (<str>,):
            return type(node.type) is ast.Str
        # raise <str>
        if node_type is ast.Raise:
            # TODO raise <expr>
            # (Where <expr> does not evaluate to exception.)
            return node.type and type(node.type) is ast.Str


class MisplacedImport(object):
    key = 'bad_import'

    def __init__(self):
        self.header = True


    def analyse_node(self, node):
        node_type = type(node)
        # import xx, from xx import yy
        if node_type is ast.Import or node_type is ast.ImportFrom:
            return not self.header

        if node_type is ast.Expr:
            if type(node.value) is not ast.Str:
                self.header = False
        elif isinstance(node, ast.stmt):
            self.header = False
        return False


ast_plugins = [ExceptAllPlugin, StringException, MisplacedImport]


###########################################################################
# The analysis code
###########################################################################

def analyse_file_by_lines(filename):
    """This function analyses a file and produces a dict with these members:
     - 'lines': number of lines;
     - 'bad_length': list of lines longer than 79 characters;
     - 'bad_end': list of lines with trailing whitespaces;
     - 'tabs': list of lines with tabulators;
    """
    # Init
    stats = {}
    for plugin in line_plugins:
        stats[plugin.key] = []

    # Encoding (FIXME hardcoded to UTF-8)
    encoding = 'utf-8'

    # Analyse
    line_no = 0
    for line in open(filename):
        line = str(line, encoding)
        # Plugins
        for plugin in line_plugins:
            if plugin.analyse_line(line):
                stats[plugin.key].append(line_no)
        # Next
        line_no += 1

    # Number of lines
    stats['lines'] = line_no
    return stats


def analyse_file_by_tokens(filename, ignore_errors):
    """This function analyses a file and produces a dict with these members:
     - 'tokens': number of tokens;
     - 'bad_indentation': list of lines with a bad indentation;
    """
    stats = {'tokens': 0}

    plugins = [ cls() for cls in token_plugins ]
    for plugin in plugins:
        stats[plugin.key] = []

    tokens = generate_tokens(open(filename).readline)
    try:
        for token, value, (srow, scol), _, _ in tokens:
            # Tokens number
            stats['tokens'] += 1

            for plugin in plugins:
                if plugin.analyse_token(token, value, srow, scol):
                    stats[plugin.key].append(srow)
    except TokenError as e:
        if ignore_errors is False:
            raise e
        print(e)
        return {'tokens': 0}

    return stats


class Visitor(ast.NodeVisitor):

    def __init__(self):
        self.plugins = [ cls() for cls in ast_plugins ]
        self.stats = {}
        for plugin in self.plugins:
            self.stats[plugin.key] = []


    def generic_visit(self, node):
        # Plugins
        for plugin in self.plugins:
            if plugin.analyse_node(node):
                self.stats[plugin.key].append(node.lineno)

        ast.NodeVisitor.generic_visit(self, node)



def analyse_file_by_ast(filename, ignore_errors):
    """This function analyses a file and produces a dict with these members:
     - 'except_all': list of line where all exceptions are catched;
     - 'string_exception': list of lines with string exceptions;
     - 'bad_import': ;
    """
    try:
        root = ast.parse(open(filename).read())
    except (SyntaxError, IndentationError) as e:
        if ignore_errors is False:
            raise e
        print(e)
        return None
    visitor = Visitor()
    visitor.generic_visit(root)
    return visitor.stats


def analyse_file(filename, ignore_errors):
    """This function merges the two dictionaries for a file
    """
    # Pass 1
    stats = analyse_file_by_lines(filename)
    # Pass 2
    stats2 = analyse_file_by_tokens(filename, ignore_errors)
    stats.update(stats2)
    # Pass 3
    stats3 = analyse_file_by_ast(filename, ignore_errors)
    if stats3 is not None:
        stats.update(stats3)

    # Ok
    return stats



def analyse(filenames, ignore_errors=False):
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
        'bad_import': 0}

    files_db = []
    for filename in filenames:
        f_stats = analyse_file(filename, ignore_errors)
        if f_stats['lines'] != 0:
            for key, value in f_stats.items():
                if type(value) is list:
                    stats[key] += len(value)
                else:
                    stats[key] += value
            f_stats['filename'] = filename
            files_db.append(f_stats)
    return stats, files_db



###########################################################################
# The four commands:
#
# - show_stats
# - show_lines
# - fix
#
###########################################################################

def print_list(title, string_list):
    if len(string_list) != 0:
        print(title)
        print('-'*len(title))
        for line in string_list:
            print(line)
        print()


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
                    print('Worse files:')
                    first = False
                print('- %s (%d)' % (f['filename'], sort_key(f)))
        if not first:
            print()


def show_lines(filenames):
    """Show number lines of errors
    """
    # We get statistics
    stats, files_db = analyse(filenames)
    # We show lines
    print()
    comments = []
    infos = files_db[0]
    for problem in problems.keys():
        lines = infos[problem]
        if lines:
            comments.append(f'Lines {problems[problem]}:\n')
            for line in lines:
                comments.append('%s +%d' % (filenames[0], line))
            comments.append('\n')
    if comments:
        print('\n'.join(comments))
    else:
        print('This file is perfect !')


def show_stats(filenames, worse):
    """Show general statistics.
    """
    # We get statistics
    stats, files_db = analyse(filenames)
    # Show quality summary
    print()
    print('Code length: %d lines, %d tokens' % (stats['lines'],
                                                stats['tokens']))
    print()

    # Aesthetics (and readibility)
    show_comments = []
    for problem in aesthetics_problems['keys']:
        stat = stats[problem]
        if stat != 0:
            pourcent = (stats[problem] * 100.0)/stats['lines']
            show_comments.append('%5.02f%% lines %s' % (pourcent,
                                    aesthetics_problems['keys'][problem]))
    print_list(aesthetics_problems['title'], show_comments)
    print_worses(files_db, worse, aesthetics_problems['keys'])

    # Exception handling
    show_comments = []
    for problem in exception_problems['keys']:
        stat = stats[problem]
        if stat != 0:
            show_comments.append('%d times %s' % (stat,
                                    exception_problems['keys'][problem]))
    print_list(exception_problems['title'], show_comments)
    print_worses(files_db, worse, exception_problems['keys'])

    # Imports
    if stats['bad_import'] != 0:
        show_comments = ['%d %s' % (stats['bad_import'],
                                    import_problems['keys']['bad_import'])]
    else:
        show_comments = []
    print_list('Imports', show_comments)
    print_worses(files_db, worse, ['bad_import'])


def fix(filenames):
    """Clean files: We remove trailing spaces & tabulators
    """
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
            if line.strip()=='':
                line = '\n'
            else:
                line = ' ' * indent + line.strip() + '\n'
            # Append
            lines.append(line)

        # Save
        open(filename, 'w').write(''.join(lines))



###########################################################################
# The command line
###########################################################################

if __name__ == '__main__':
    # The parser
    usage = '%prog [OPTIONS] [FILES]'
    version = f'itools {itools.__version__}'
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
    worktree = open_worktree('.', soft=True)
    if args:
        filenames = set([])
        for arg in args:
            filenames = filenames.union(glob(arg))
        filenames = list(filenames)
    elif worktree:
        filenames = worktree.get_filenames()
        filenames = [ x for x in filenames if x.endswith('.py') ]
    else:
        filenames = []
        for path in lfs.traverse():
            if lfs.is_file(path) and basename(path).endswith('.py'):
                filenames.append(relpath(path))

    # Check options
    if len(filenames) == 0:
        parser.error('Please give at least one file to analyse.')
    if options.worse > 0 and options.show_lines is True:
        parser.error(
            'Options --worse and --show-lines are mutually exclusive.')
    if options.show_lines == True and len(filenames) != 1:
        parser.error(
            'The option --show-lines takes one file in parameter.')

    # (1) Show Lines
    if options.show_lines:
        show_lines(filenames)

    # (2) Fix
    elif options.fix is True:
        show_stats(filenames, options.worse)
        print('FIXING...')
        fix(filenames)
        print('DONE')
        show_stats(filenames, options.worse)

    # (3) Analyse
    else:
        show_stats(filenames, options.worse)

