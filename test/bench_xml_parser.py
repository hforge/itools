# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008      Henry Obein <henry@itaapy.com>
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
import gc
from gzip import GzipFile
from math import log as math_log
from optparse import OptionParser
from os.path import join
from string import center, ljust, rjust
from tarfile import open as open_tar
from xml.parsers.expat import ParserCreate, ExpatError

# Import from itools
import itools
import itools.http
from itools.utils import vmsize, get_time_spent
from itools.vfs import vfs
from itools.xml import XMLParser, XMLError, START_ELEMENT, END_ELEMENT

#####################################################################
# UTILS
#####################################################################
def get_string_size(bytes):
    units = [' b','Kb','Mb','Gb','Tb']
    if not bytes:
        return '0  b'
    exponent = int(math_log(bytes, 1024))
    if exponent > 4:
        return '%d  b' % bytes
    value = bytes / 1024.0 ** exponent, units[exponent]
    return '%6.2f %s' % value


def get_string_time(s):
    # µs
    micro_s = s * 1000000.0
    ms, micro_s = divmod(micro_s, 1000)
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    if d:
        # days
        return u'%6.2f d ' % (d + h / 24.0)
    elif h:
        # hours
        return u'%6.2f h ' % (h + m / 60.0)
    elif m:
        # minutes
        return u'%6.2f mn' % (m + s / 60.0)
    elif s:
        # seconds
        return u'%6.2f s ' % (s + ms / 1000.0)
    elif ms:
        # milliseconds
        return u'%6.2f ms' % (ms + micro_s / 1000.0)
    else:
        # microseconds
        return u'%6.2f µs' % (micro_s + ms / 1000.0)


def get_clock_nb_pass(size):
    """
    Return the number of pass according the file size
    """

    if size < 10000: # ~ 10 KB
        return 10000
    elif size < 100000: # ~ 100 KB
        return 100
    elif size < (1024 * 1024): # 1 MB
        return 50
    elif size < (1024 * 1024 * 10): # 10 MB
        return 3
    elif size < (1024 * 1024 * 50): # 50 MB
        return 2
    return 1


def get_test_filenames(test_path, force_download):
    """Return the test file names
    If the test files does'nt exists, we download it
    """

    uris = {'http://download.wikimedia.org/qualitywiki/latest':
            [('qualitywiki-latest-stub-articles.xml', '.gz'),      #~  3.1 KB
             ('qualitywiki-latest-stub-meta-current.xml', '.gz'),  #~ 11.0 KB
             ('qualitywiki-latest-stub-meta-history.xml', '.gz')], #~ 28.9 KB
            'http://download.wikimedia.org/tawiki/latest':
            [('tawiki-latest-stub-articles.xml', '.gz'),           #~ 1.2 MB
             ('tawiki-latest-stub-meta-history.xml', '.gz')],      #~ 7.3 MB
            'http://www.w3.org/XML/Test/': [('xmlts20080205', '.tar.gz')]
            }
    compressed_dir_path = join(test_path, 'compressed_files')

    if force_download is True:
        if vfs.exists(compressed_dir_path):
            print 'Remove compressed directory ', compressed_dir_path
            vfs.remove(compressed_dir_path)
            for names in uris.itervalues():
                for (name, ext) in names:
                    path = join(test_path, name)
                    if vfs.exists(path):
                        print 'Remove %s file' % path
                        vfs.remove(path)

    # test directory
    if vfs.exists(test_path) is False:
        vfs.make_folder(test_path)

    # compressed directory
    if vfs.exists(compressed_dir_path) is False:
        compressed_dir = vfs.make_folder(compressed_dir_path)
    else:
        compressed_dir = vfs.open(compressed_dir_path)

    test_dir_filenames = vfs.get_names(test_path)
    for base_uri, names in uris.iteritems():
        for (name, ext) in names:
            if test_dir_filenames.count(name):
                continue
            compressed_dest = join(compressed_dir_path, '%s%s' % (name, ext))
            # check if tarball already exists
            if vfs.exists(compressed_dest) is False:
                src = join(base_uri, '%s%s' % (name, ext))
                print 'GET %s file' % src
                dest = join(test_path, name)
                if vfs.exists(src) is False:
                    print "%s uri does not exists" % src
                    continue
                src_file = vfs.open(src)
                # save Gzip file
                compressed_dest_file = vfs.make_file(compressed_dest)
                compressed_dest_file.write(src_file.read())
                compressed_dest_file.close()
                src_file.close()
            print 'Extract file %s' % compressed_dest
            # Uncompressed File Path
            if name == 'xmlts20080205':
                # uncompress onky xmlconf.xml file
                tar = open_tar(compressed_dest)
                xmlconf_file = tar.extractfile('xmlconf/xmlconf.xml')
                ucf_path = join(test_path, name)
                ucf_file = vfs.make_file(ucf_path)
                ucf_file.write(xmlconf_file.read())
                ucf_file.close()
            else:
                # untar Gzip file
                compressed_dest_file = vfs.open(compressed_dest)
                gzip_file = GzipFile(compressed_dest)
                ucf_path = join(test_path, name)
                ucf_file = vfs.make_file(ucf_path)
                ucf_file.write(gzip_file.read())
                compressed_dest_file.close()
                gzip_file.close()
                ucf_file.close()

    tests = []
    # update test dir name
    test_dir_filenames = vfs.get_names(test_path)
    for filename in test_dir_filenames:
        real_path = join(test_path, filename)
        if vfs.is_file(real_path):
            bytes = vfs.get_size(real_path)
            tests.append((real_path, filename, bytes,
                          get_string_size(bytes)))
    tests.sort(key=lambda x: x[2])
    return tests


#####################################################################
# EXPAT
#####################################################################
# Expat call back
def start_element(name, attrs):
    pass
def end_element(name):
    pass
def char_data(data):
    pass


def expat_parser_file_mode(xml, nb_repeat):
    """xml is an open file object"""
    v0 = vmsize()
    t0 = get_time_spent(mode='both')
    for i in nb_repeat:
        # Raise MemoryError after calling seek(0)
        # if we don't create a new parser
        p = ParserCreate()
        p.StartElementHandler = start_element
        p.EndElementHandler = end_element
        p.ParseFile(xml)
        xml.seek(0)
    t1 = get_time_spent(mode='both', since=t0)
    v1 = vmsize()

    time_spent = get_string_time(t1 / float(len(nb_repeat)))
    memo = v1 -v0

    return time_spent, memo


#####################################################################
# ITOOLS
#####################################################################
def itools_parser_file_mode(xml, nb_repeat):
    v0 = vmsize()
    t0 = get_time_spent(mode='both')
    for i in nb_repeat:
        parser = XMLParser(xml)
        for type, value, line in parser:
            if type == START_ELEMENT:
                pass
            elif type == END_ELEMENT:
                pass
        xml.seek(0)
    t1 = get_time_spent(mode='both', since=t0)
    v1 = vmsize()

    time_spent = get_string_time((t1-t0) / float(len(nb_repeat)))
    memo = v1 -v0

    return time_spent, memo


#####################################################################
# BENCHMARK
#####################################################################
def bench_itools_parser(filename, nb_repeat):
    xml = open(filename)

    success = False
    time_spent = 0.0
    memory = 0.0
    str_error = u''

    try:
        time_spent, memory = itools_parser_file_mode(xml, nb_repeat)
        success = True
    except XMLError, e:
        str_error = str(e)
    except Exception, e2:
        str_error = str(e2)
    xml.close()

    return success, time_spent, memory, str_error


def bench_expat_parser(filename, nb_repeat):
    xml = open(filename)

    success = False
    time_spent = 0.0
    memory = 0.0
    str_error = u''

    try:
        time_spent, memory = expat_parser_file_mode(xml, nb_repeat)
        success = True
    except ExpatError, e:
        str_error = str(e)
    except Exception, e2:
        str_error = str(e2)
    xml.close()

    return success, time_spent, memory, str_error


#####################################################################
# OUPUT
#####################################################################
def output_init(parsers_name):
    """
30c | 23c | 23c -> 78c
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
          itools        |         expat         |             file
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 ___.___ ms / ___.___ KB|___.___ ms / ___.___ KB|qualitywiki-late (___.___ KB)
                        |                       |
    """

    print u'-' * 78
    print u' %s|%s|%s' % (center(u'file', 30), center(parser_names[0], 23),
                          center(parser_names[1], 23))
    print u'-' * 78



def output_result(results, file):
    # file output
    filename, file_size = file
    filename = ljust(filename[:19], 19)
    file_size = get_string_size(file_size)
    file_size = rjust(file_size[:9], 9)
    file_string = u'%s  %s' % (filename, file_size)

    parser_output = u''
    # output 1
    parser_name, result = results[0]
    success1, time_spent, memory, err1 = result
    memory = get_string_size(memory)
    if success1:
        # time_spent ok already like ___.___ ms or s or mn
        output1 = rjust(u'%s / %s' % (time_spent, memory), 21)
    else:
        output1 = center(u'FAILED',  21)

    # output 2
    parser_name, result = results[1]
    success2, time_spent, memory, err2 = result
    memory = get_string_size(memory)
    if success2:
        # time_spent ok already like ___.___ ms or s or mn
        output2 = rjust(u'%s / %s' % (time_spent, memory), 21)
    else:
        output2 = center(u'FAILED',  21)

    print '%s | %s | %s ' % (file_string, output1, output2)


#####################################################################
# MAIN
#####################################################################
if __name__ == '__main__':
    usage = '%prog [OPTIONS]'
    version = 'itools %s' % itools.__version__
    description = ('XML Parser benchmark')
    parser = OptionParser(usage, version=version, description=description)
    parser.add_option('', '--expat-before',
                      help='Call Expat parser before itools parser',
                      default=False, dest='expat_before', action="store_true")
    parser.add_option('', '--no-gc',
                      help='Disable automatic garbage collection.',
                      default=False, dest='no_gc', action="store_true")
    parser.add_option('-p', '--nb-pass', help='Number of pass',
                      default=1, type='int', dest='nb_pass')
    parser.add_option('-d', '--directory',
                      help=('An optional  directory  to  which  to'
                             'extract  files.'),
                      default='/tmp/itools_bench', dest='test_dir')
    parser.add_option('', '--force-download',
                      help='Force the test files download.',
                      default=False, dest='force_download', action="store_true")

    options, args = parser.parse_args()
    nb_pass  = options.nb_pass
    # garbage collector
    if options.no_gc is True:
        print u'DISABLE GARBAGE COLLECTOR'
        gc.disable()

    # get test files
    filenames = get_test_filenames(options.test_dir, options.force_download)
    test_length = len(filenames)

    expat_before = options.expat_before
    print u'NB TEST', test_length

    parser_functions = {'expat': bench_expat_parser,
                        'itools': bench_itools_parser}

    for pass_id in range(0, options.nb_pass):
        print u'PASS %s / %s' % ((pass_id + 1), nb_pass)
        if expat_before is True:
            parser_names = ['expat', 'itools']
        else:
            parser_names = ['itools', 'expat']
        expat_before = not expat_before

        output_init(parser_names);
        for index, data in enumerate(filenames):
            # init pass result
            pass_results = {'itools': None, 'expat': None}
            # get data
            real_path, filename, file_bytes, file_size = data
            nb_repeat = get_clock_nb_pass(file_bytes)
            test_results = []
            for parser_name in parser_names:
                fn = parser_functions[parser_name]
                results = fn(real_path, range(0, nb_repeat))
                success, time_spent, memory, err = results

                test_results.append((parser_name, results))
            output_result(test_results, (filename, file_bytes))
        print
