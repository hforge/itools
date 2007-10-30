#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 David Versmisse <david.versmisse@itaapy.com>
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
from optparse import OptionParser
from subprocess import call
from tempfile import TemporaryFile
from StringIO import StringIO
from token import tok_name
import tokenize

# Import from itools
import itools
from itools import git


#Globals variables
verbosity = 0


def print_file_error(filename, line, message):
    global verbosity
    if verbosity >= 2:
        print '%s:%d:%s'%(filename, line, message)

def analyse_file_pass1(filename):
    """
    This function analyses a file and produces a dict with these members:
     - 'lines': Number of lines;
     - 'bad_lenght': true if the lenght > 79
     - 'bad_end': true if there are spaces or tabs at the end of the line;
    """

    stats = {
        'lines': 0,
        'bad_lenght': 0,
        'bad_end': 0}

    for line in file(filename):
        #Number of line
        stats['lines'] += 1

        #Bad lenght
        if len(line.rstrip()) > 79:
            stats['bad_lenght'] += 1
            print_file_error(filename, stats['lines'],
                            'bad lenght')

        #Bad end
        if len(line.rstrip()) != len(line.rstrip('\n\x0b\x0c\r')):
            stats['bad_end'] += 1
            print_file_error(filename, stats['lines'],
                            'bad end')

    return stats


def analyse_file_pass2(filename):
    """
    This function analyses a file and produces a dict with these members:
     - 'tokens': number of tokens;
     - 'imports': number of import;
     - 'bad_import': number of bad import;
     - 'excepts': number of except;
     - 'bad_except': number of bad except;
     - 'raise': number of raise;
     - 'bad_raise': number of bad raise;
     - 'bad_indentation': number of lines with a bad indentation;
     - 'syntax_error': number of lines with an error;
    """

    stats = {
        'tokens': 0,
        'imports': 0,
        'bad_import': 0,
        'excepts': 0,
        'bad_except': 0,
        'raises': 0,
        'bad_raise': 0,
        'bad_indentation':0,
        'syntax_error': 0}
    try:
        tokens = tokenize.generate_tokens(file(filename).readline)

        last_name = ''
        current_line = 0
        current_indentation = 0

        header = True
        command_on_line = False
        import_on_line = False

        for type,value,begin,end,_ in tokens:
            #Tokens number
            stats['tokens'] += 1

            #Find the line number
            if begin[0] > current_line:
                current_line = begin[0]

            #Find NEWLINE
            if tok_name[type] == 'NEWLINE':
                #print 'NEWLINE [%d]'%current_line
                if command_on_line and not import_on_line:
                    header = False
                command_on_line = False
                import_on_line = False


            #Find command
            if tok_name[type] not in [
                'COMMENT', 'STRING', 'NEWLINE', 'NL']:
                command_on_line = True
            #Find import and test
            if tok_name[type] == 'NAME' and value == 'import':
                import_on_line = True
                if not header:
                    stats['bad_import'] += 1
                    print_file_error(filename, current_line,
                                    'bad import')

            #Indentation management
            if tok_name[type] == 'INDENT':
                if '\t' in value or len(value) - current_indentation != 4:
                    stats['bad_indentation'] += 1
                    print_file_error(filename, current_line,
                                    'bad indentation')
                current_indentation = len(value)
            if tok_name[type] == 'DEDENT':
                current_indentation = begin[1]

            #import, except and raise number
            if (tok_name[type] == 'NAME' and
                value in ['import', 'except', 'raise']):
                stats[value+'s'] += 1

            #except: or except '...' ?
            if last_name == 'except' and (
                (tok_name[type] == 'STRING') or
                (tok_name[type] == 'OP' and value == ':')):
                stats['bad_except'] += 1
                print_file_error(filename, current_line,
                                'bad except')

            #raise '...' ?
            if last_name == 'raise' and  tok_name[type] == 'STRING':
                stats['bad_raise'] += 1
                print_file_error(filename, current_line,
                                'bad raise')

            #Last_name
            if tok_name[type] == 'NAME':
                last_name = value
            else:
                last_name = ''

    except tokenize.TokenError, IndentationError:
        stats['syntax_error'] = 1
        print_file_error(filename, current_line,
                        'syntax error')

    return stats


def analyse_file(filename):
    stats={}

    stats1 = analyse_file_pass1(filename)
    for key, value in stats1.iteritems():
        stats[key] = value

    stats2 = analyse_file_pass2(filename)
    for key, value in stats2.iteritems():
        stats[key] = value

    return stats


def analyse(filenames):
    #Gravity indicators
    weight={
        'bad_lenght': 10,
        'bad_end': 1,
        'bad_import': 50,
        'bad_except': 40,
        'bad_raise': 100,
        'bad_indentation': 10,
        'syntax_error': 1000}

    stats={
        'lines': 0,
        'bad_lenght': 0,
        'bad_end': 0,
        'tokens': 0,
        'imports': 0,
        'bad_import': 0,
        'excepts': 0,
        'bad_except': 0,
        'raises': 0,
        'bad_raise': 0,
        'bad_indentation': 0,
        'syntax_error': 0}

    for key in stats.iterkeys():
        weight.setdefault(key,0)

    files = []
    for filename in filenames:
        f_stats = analyse_file(filename)
        if f_stats['lines'] != 0:
            bad_sum = 0.0
            for key, value in f_stats.iteritems():
                stats[key] += value
                bad_sum += weight[key]*value

            bad_sum = bad_sum/f_stats['lines']
            files.append((bad_sum, filename))

    # Show quality summary
    if verbosity == 0:
        print 'Total number of files with syntax errors: %d' % \
              stats['syntax_error']
        print 'Total number of lines: %d and %d tokens' %(stats['lines'],
                                                          stats['tokens'])

        value = (stats['bad_indentation']*100.0)/stats['lines']
        print ' - with bad indentation           : %.02f%%' % value

        value = (stats['bad_lenght']*100.0)/stats['lines']
        print ' - with bad lenght (>79)          : %.02f%%' % value

        value = (stats['bad_end']*100.0)/stats['lines']
        print ' - with bad end (with " " or "\\t"): %.02f%%' % value

        for name in ['import','except','raise']:
            if stats[name+'s'] != 0:
                value = (stats['bad_'+name]*100.0)/stats[name+'s']
                print ' - with bad %6s/good %6ss   : %.02f%%' %(
                    name, name, value)

    # Show list of worse files
    if verbosity == 1:
        print 'Worse files: filename (gravity)'
        print
        files.sort()
        files.reverse()
        files = files[:3]
        for gravity, filename in files:
            if gravity > 0.0:
                print ' - %s (%f)' %(filename, gravity)
                f_stats = analyse_file(filename)
                errors = []
                for key, value in f_stats.iteritems():
                    errors.append((weight[key],value,key))
                errors.sort()
                errors.reverse()
                count = 3
                for error in errors:
                    if error[0] != 0 and error[1] != 0 :
                        print '   * %s in %d line(s)'%(error[2],error[1])
                        count -= 1
                        if count == 0:
                            break


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

    parser.add_option('-v', action='count', dest='verbosity',
                      help="to run in verbose mode, -vv is more verbose")
    parser.set_defaults(verbosity=0)

    options, args = parser.parse_args()
    verbosity = options.verbosity

    #Making of filenames
    if args:
        filenames = args
    elif git.is_available():
        filenames = git.get_filenames()
        filenames = [ x for x in filenames if x.endswith('.py') ]
    else:
        file = TemporaryFile()
        call(['find', '-name', '*.py'], stdout=file)
        file.seek(0)
        filenames = [ x.strip() for x in file.readlines() ]
        file.close()

    # Analyse
    analyse(filenames)

    # Fix
    if options.fix is True:
        print 'FIXING...'
        fix(filenames)
        print 'DONE'
        analyse(filenames)
