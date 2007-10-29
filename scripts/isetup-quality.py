#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
verbose = False

def analyse_line(line):
    """
    This function analyses a line and produces a dict with these members:
     - 'lenght': lenght of the line without '\n' or everything else;
     - 'spaces': number of space characters at the beginning of the line;
     - 'tokens': number of tokens;
     - 'import': boolean;
     - 'command': True if the line has a least one token != COMMENT;
     - 'bad_end': True if there are spaces or tabs at the end of the line;
     - 'tabs': boolean;
     - 'bad_except': boolean;
     - 'bad_raise': boolean;
    """

    result={
        'lenght': len(line.rstrip()),
        'spaces': 0, 
        'tokens': 0,
        'import': False,
        'command': False,
        'tabs': False,
        'bad_end': len(line.rstrip()) != len(line.rstrip('\n\x0b\x0c\r')),
        'bad_except': False,
        'bad_raise': False}


    try:
        tokens=tokenize.generate_tokens(StringIO(line).readline)
        last_name = ''
     
        for type,value,begin,end,_ in tokens:
            #The end ??
            if begin[0] == 2 or tok_name[type] in [
                'NL','ENDMARKER', 'NEWLINE', 'ERRORTOKEN']:
                break

            #Looking for spaces and tabs characters       
            if tok_name[type] == 'INDENT':
                for c in value:
                    if c == ' ':
                        result['spaces'] += 1
                    #Tabulation is bad and equal to 8 spaces
                    elif c == '\t':
                        result['tabs'] = True
                        result['spaces'] += 8
                continue

            result['tokens'] += 1

            #Looking for Comment
            if tok_name[type] == 'COMMENT':
                last_name = ''
                continue

            #This is a command !
            result['command'] = True

            #except: or except '...' ?
            if last_name == 'except' and (
                value == ':' or tok_name[type] == 'STRING'):

                result['bad_except'] = True

            #raise '...' ?
            if last_name == 'raise' and  tok_name[type] == 'STRING':
                result['bad_raise'] = True 

            #import ?
            if value == 'import':
                result['import'] = True
            
            if tok_name[type] == 'NAME':
                last_name=value
            else:
                last_name = ''
                
    except tokenize.TokenError:
        #This is certainly a multi-line, we pass
        pass
    return result

def print_file_error(filename, line_number, error_msg):
    global verbose
    if verbose:
        print "%s:%d:%s"%(filename, line_number, error_msg)

def analyse_file(filename):
    """
    This function analyses a file and produces a dict with these members:
     - 'lines': number of lines;
     and 7 indicators:
     - 'tokens'
     - 'bad_indentation'
     - 'bad_lenght'
     - 'bad_end'
     - 'imports'
     - 'bad_import'
     - 'bad_except'
     - 'bad_raise'
    """

    stats={
        'lines': 0,
        'tokens': 0,
        'bad_indentation': 0,
        'bad_lenght': 0,
        'bad_end': 0,
        'imports': 0,
        'bad_import': 0,
        'bad_except': 0,
        'bad_raise': 0}

    header = True
    indent = 0
    for line in open(filename).readlines():
        stats['lines'] += 1
        result = analyse_line(line)
        stats['tokens'] += result['tokens']

        #Yet in the header ?
        if result['command'] and not result['import']:
            header = False

        #Indentation ?
        diff_indent = result['spaces']-indent
        if ( (diff_indent > 0 and diff_indent != 4) or
             result['tabs']):
            stats['bad_indentation'] += 1
            print_file_error(filename, stats['lines'],
                             'bad indentation')
            
        indent = result['spaces']

        #Lenght ?
        if result['lenght'] > 79:
            stats['bad_lenght'] += 1
            print_file_error(filename, stats['lines'],
                             'bad lenght')
            
        #Bad end ?
        if result['bad_end']:
            stats['bad_end'] += 1
            print_file_error(filename, stats['lines'],
                             'bad end')
        
         #Import and misplaced import
        if result['import']:
            stats['imports'] += 1
            if not header:
                stats['bad_import'] += 1
                print_file_error(filename, stats['lines'],
                                 'bad import')

        #Bad except ?
        if result['bad_except']:
            stats['bad_except'] += 1
            print_file_error(filename, stats['lines'],
                             'bad except')

        #Bad raise ?
        if result['bad_raise']:
            stats['bad_raise'] += 1
            print_file_error(filename, stats['lines'],
                             'bad raise')


    return stats



def analyse(filenames):
    stats={
        'lines': 0,
        'tokens': 0,
        'bad_indentation': 0,
        'bad_lenght': 0,
        'bad_end': 0,
        'imports': 0,
        'bad_import': 0,
        'bad_except': 0,
        'bad_raise': 0}

    files = []
    for filename in filenames:
        f_stats = analyse_file(filename)

        bad_sum = 0.0
        for key, value in f_stats.iteritems():
            stats[key] += value
            if key not in ['lines', 'tokens', 'imports']:
                bad_sum += value
                
        bad_sum = bad_sum/stats['lines']
        files.append((bad_sum, filename))

    # Show quality summary
    print 'Total number of lines: %d' % stats['lines']
    print

    value = float(stats['tokens'])/stats['lines']
    print ' - Average numbers of tokens/line           : %.02f' % value   
    
    value = (stats['bad_indentation']*100.0)/stats['lines']
    print ' - with bad indentation                     : %.02f%%' % value

    value = (stats['bad_lenght']*100.0)/stats['lines']
    print ' - with bad lenght (>79)                    : %.02f%%' % value

    value = (stats['bad_end']*100.0)/stats['lines']
    print ' - with bad end (with " " or "\\t")          : %.02f%%' % value
 

    if stats['imports'] != 0:
        value = (stats['bad_import']*100.0)/stats['imports']
    print ' - with bad import/good imports             : %.02f%%' % value

    value = (stats['bad_except']*100.0)/stats['lines']
    print ' - with bad except (except: or except "..."): %.02f%%' % value

    value = (stats['bad_raise']*100.0)/stats['lines']
    print ' - with bad raise (raise "...")             : %.02f%%' % value
    print
    # Show list of worse files
    print 'Worse files:'
    print
    files.sort()
    files.reverse()
    files = files[:3]
    for weight, filename in files:
        print ' - %s' % filename
    print



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
        '-v', '--verbose', action='store_true', dest='verbose',
        help="to run in verbose mode")
    options, args = parser.parse_args()
    verbose = bool(options.verbose)

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
