#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2007 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from the Standard Library
import ast
from ast import parse, NodeVisitor
from datetime import date
from glob import glob
from optparse import OptionParser
from os import getcwd, chdir
from subprocess import call
from sys import exit, stdout
from tempfile import mkdtemp
from time import time
from tokenize import COMMENT, DEDENT, INDENT, NAME, NEWLINE, NL, OP, STRING
from tokenize import generate_tokens, TokenError

# Import from Matplotlib
create_graph_is_available = True
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.dates import DateFormatter
    from matplotlib.ticker import FormatStrFormatter
except ImportError:
    create_graph_is_available = False

# Import from itools
import itools
from itools.core import merge_dicts
from itools import git, vfs


# Define list of problems
code_length = {
    'title': u'Code length',
    'keys': {'lines': u'Number of lines', 'tokens': u'Number of tokens'},
    'pourcent': False}

aesthetics_problems = {
     'title': u'Aesthetics (and readibility)',
     'keys': {'tabs':  u'with tabulators',
              'bad_indentation': u'bad indented',
              'bad_length': u'longer than 79 characters',
              'bad_end': u'with trailing whitespaces'},
     'pourcent': True}

exception_problems = {
    'title': u'Exception handling',
    'keys': {
        'string_exception': u'string exceptions are used',
        'except_all': u'all exceptions are catched'},
    'pourcent': False}

import_problems = {
    'title': u'Import problems',
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
        return len(line.rstrip()) != len(line.rstrip(u'\n\x0b\x0c\r'))


class TabsPlugin(object):
    key = 'tabs'

    @classmethod
    def analyse_line(self, line):
        return u'\t' in line


line_plugins = [LineLengthPlugin, TrailingSpacePlugin, TabsPlugin]


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
    for line in file(filename):
        line = unicode(line, encoding)
        # Plugins
        for plugin in line_plugins:
            if plugin.analyse_line(line):
                stats[plugin.key].append(line_no)
        # Next
        line_no += 1

    # Number of lines
    stats['lines'] = line_no
    return stats


def analyse_file_by_tokens(filename):
    """This function analyses a file and produces a dict with these members:
     - 'tokens': number of tokens;
     - 'bad_indentation': list of lines with a bad indentation;
    """
    stats = {
        'tokens': 0,
        'bad_indentation': []}

    srow = 0
    current_indentation = 0
    tokens = generate_tokens(file(filename).readline)

    for tok_type, value, (srow, scol), _, _ in tokens:
        # Tokens number
        stats['tokens'] += 1

        # Indentation management
        if tok_type == INDENT:
            if '\t' in value or len(value) - current_indentation != 4:
                stats['bad_indentation'].append(srow)
            current_indentation = len(value)
        if tok_type == DEDENT:
            current_indentation = scol

    return stats


class Visitor(NodeVisitor):

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

        NodeVisitor.generic_visit(self, node)



def analyse_file_by_ast(filename):
    """This function analyses a file and produces a dict with these members:
     - 'except_all': list of line where all exceptions are catched;
     - 'string_exception': list of lines with string exceptions;
     - 'bad_import': ;
    """
    ast = parse(open(filename).read())
    visitor = Visitor()
    visitor.generic_visit(ast)
    return visitor.stats



def analyse_file(filename):
    """This function merges the two dictionaries for a file
    """
    # Pass 1
    stats = analyse_file_by_lines(filename)
    # Pass 2
    stats2 = analyse_file_by_tokens(filename)
    stats.update(stats2)
    # Pass 3
    stats3 = analyse_file_by_ast(filename)
    stats.update(stats3)

    # Ok
    return stats



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
        'bad_import': 0}

    files_db = []
    for filename in filenames:
        f_stats = analyse_file(filename)
        if f_stats['lines'] != 0:
            for key, value in f_stats.iteritems():
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
# - create_graph
#
###########################################################################

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


def show_lines(filenames):
    """Show number lines of errors
    """
    # We get statistics
    stats, files_db = analyse(filenames)
    # We show lines
    print
    comments = []
    infos = files_db[0]
    for problem in problems.keys():
        lines = infos[problem]
        if lines:
            comments.append('Lines %s:\n' % problems[problem])
            for line in lines:
                comments.append('%s +%d' % (filenames[0], line))
            comments.append('\n')
    if comments:
        print '\n'.join(comments)
    else:
        print u'This file is perfect !'


def show_stats(filenames, worse):
    """Show general statistics.
    """
    # We get statistics
    stats, files_db = analyse(filenames)
    # Show quality summary
    print
    print 'Code length: %d lines, %d tokens' % (stats['lines'],
                                                stats['tokens'])
    print

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



def create_graph():
    """Create graph of code quality evolution
    """
    t0 = time()
    cwd = getcwd()
    project_name = cwd.split('/')[-1]
    # We copy project to tmp (for security)
    tmp_directory = '%s/ipkg_quality.git' % mkdtemp()
    call(['git', 'clone',  cwd, tmp_directory])
    chdir(tmp_directory)
    # First step: we create a list of statistics
    statistics = {}
    commit_ids = git.get_revisions()
    commit_ids.reverse()
    print 'Script will analyse %s commits.' % len(commit_ids)
    for commit_id in commit_ids:
        # We move to a given commit
        call(['git', 'reset', '--hard', commit_id])
        # Print script evolution
        stdout.write('.')
        stdout.flush()
        # We list files
        filenames = git.get_filenames()
        filenames = [ x for x in filenames if x.endswith('.py') ]
        # We get code quality for this files
        stats, files_db = analyse(filenames)
        metadata = git.get_metadata()
        date_time = metadata['committer'][1]
        commit_date = date(date_time.year, date_time.month, date_time.day)
        if commit_date not in statistics:
            statistics[commit_date] = stats
        else:
            # Same day => Avg
            for key in statistics[commit_date]:
                avg = (statistics[commit_date][key] + stats[key])/2
                statistics[commit_date][key] = avg
    print
    # Get dates
    values = []
    dates = statistics.keys()
    dates.sort()
    for a_date in dates:
        values.append(statistics[a_date])
    # Base graph informations
    base_title = '[%s %s]' % (project_name, git.get_branch_name())
    # We generate graphs
    chdir(cwd)
    for problem_dict in ['code_length', 'aesthetics_problems',
                         'exception_problems', 'import_problems']:
        current_problems = eval(problem_dict)
        graph_title = '%s %s' % (base_title, current_problems['title'])
        lines = []
        labels = []
        fig = Figure()
        graph = fig.add_subplot(111)
        for key in current_problems['keys']:
            if current_problems['pourcent']:
                problem_values = [((x[key]*100.0)/x['lines']) for x in values]
            else:
                problem_values = [x[key] for x in values]
            lines.append(graph.plot_date(dates, problem_values, '-'))
            labels.append(current_problems['keys'][key])
        graph.set_title(graph_title)
        graph.xaxis.set_major_formatter(DateFormatter("%b '%y'"))
        if current_problems['pourcent']:
            graph.set_ylabel('Pourcent')
            graph.yaxis.set_major_formatter(FormatStrFormatter("%5.02f %%"))
        else:
            graph.set_ylabel('Quantity')
        graph.set_xlabel('')
        graph.autoscale_view()
        graph.grid(True)
        fig.autofmt_xdate()
        fig.set_figheight(fig.get_figheight()+5)
        legend = fig.legend(lines, labels, loc=8, axespad=0.0)
        legend.get_frame().set_linewidth(0)
        canvas = FigureCanvasAgg(fig)
        destination = 'graph_%s.png' % problem_dict
        canvas.print_figure(destination, dpi=80)
        print '%s -> %s ' % (graph_title, destination)
    t1 = time()
    print 'Generation time: %d minutes.' % ((t1 - t0)/60)


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

    # Show graph
    parser.add_option('-g', '--graph', action="store_true", dest='graph',
                      default=False,
                      help='create graphs of code quality evolution.')

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
    if len(filenames) == 0:
        parser.error(u'Please give at least one file to analyse.')
    if options.worse > 0 and options.show_lines is True:
        parser.error(
            u'Options --worse and --show-lines are mutually exclusive.')
    if options.show_lines == True and len(filenames) != 1:
        parser.error(
            u'The option --show-lines takes one file in parameter.')

    # (1) Export graph
    if options.graph:
        # Check if GIT is available
        if not git.is_available():
            parser.error(u'Error, your project must be versioned with GIT.')
        # Check if create_graph is available
        if not create_graph_is_available:
            parser.error(u'Please install matplotlib.')
        create_graph()

    # (2) Show Lines
    elif options.show_lines:
        show_lines(filenames)

    # (3) Fix
    elif options.fix is True:
        show_stats(filenames, options.worse)
        print 'FIXING...'
        fix(filenames)
        print 'DONE'
        show_stats(filenames, options.worse)

    # (4) Analyse
    else:
        show_stats(filenames, options.worse)

