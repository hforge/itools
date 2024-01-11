# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@supinfo.com>
# Copyright (C) 2008 Henry Obein <henry.obein@gmail.com>
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

# Import from the Standard Library
import gc
from gzip import GzipFile
from math import log as math_log
from optparse import OptionParser
from os.path import join
from string import center, ljust, rjust
from subprocess import call
from tarfile import open as open_tar

# Import from itools
import itools
from itools.core import vmsize, get_time_spent
from itools.fs import lfs


#####################################################################
# UTILS
#####################################################################
def get_string_size(bytes):
    units = [' b', 'Kb', 'Mb', 'Gb', 'Tb']
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
        return '%6.2f d ' % (d + h / 24.0)
    elif h:
        # hours
        return '%6.2f h ' % (h + m / 60.0)
    elif m:
        # minutes
        return '%6.2f mn' % (m + s / 60.0)
    elif s:
        # seconds
        return '%6.2f s ' % (s + ms / 1000.0)
    elif ms:
        # milliseconds
        return '%6.2f ms' % (ms + micro_s / 1000.0)
    else:
        # microseconds
        return '%6.2f µs' % (micro_s + ms / 1000.0)


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

    uris = {'https://dumps.wikimedia.org/qualitywiki/latest/':
            [('qualitywiki-latest-stub-articles.xml', '.gz'),      #~  3.1 KB
             ('qualitywiki-latest-stub-meta-current.xml', '.gz'),  #~ 11.0 KB
             ('qualitywiki-latest-stub-meta-history.xml', '.gz')], #~ 28.9 KB
            'https://dumps.wikimedia.org/tawiki/latest/':
            [('tawiki-latest-stub-articles.xml', '.gz'),           #~ 1.2 MB
             ('tawiki-latest-stub-meta-history.xml', '.gz')],      #~ 7.3 MB
            'http://www.w3.org/XML/Test/': [('xmlts20080205', '.tar.gz')]
            }
    compressed_dir_path = join(test_path, 'compressed_files')

    if force_download is True:
        if lfs.exists(compressed_dir_path):
            print('Remove compressed directory ', compressed_dir_path)
            lfs.remove(compressed_dir_path)
            for names in uris.itervalues():
                for (name, ext) in names:
                    path = join(test_path, name)
                    if lfs.exists(path):
                        print('Remove %s file' % path)
                        lfs.remove(path)

    # test directory
    if lfs.exists(test_path) is False:
        lfs.make_folder(test_path)

    # compressed directory
    if lfs.exists(compressed_dir_path) is False:
        lfs.make_folder(compressed_dir_path)
    else:
        lfs.open(compressed_dir_path)

    test_dir_filenames = lfs.get_names(test_path)
    for base_uri, names in uris.items():
        for (name, ext) in names:
            if test_dir_filenames.count(name):
                continue
            compressed_dest = join(compressed_dir_path, '%s%s' % (name, ext))
            # check if tarball already exists
            if lfs.exists(compressed_dest) is False:
                src = join(base_uri, '%s%s' % (name, ext))
                print('GET %s file' % src)
                if lfs.exists(src) is False:
                    print("%s uri does not exists" % src)
                    continue
                src_file = lfs.open(src)
                # save Gzip file
                compressed_dest_file = lfs.make_file(compressed_dest)
                compressed_dest_file.write(src_file.read())
                compressed_dest_file.close()
                src_file.close()
            print('Extract file %s' % compressed_dest)
            # Uncompressed File Path
            if name == 'xmlts20080205':
                # uncompress only xmlconf.xml file
                tar = open_tar(compressed_dest)
                xmlconf_file = tar.extractfile('xmlconf/xmlconf.xml')
                ucf_path = join(test_path, name)
                ucf_file = lfs.make_file(ucf_path)
                ucf_file.write(xmlconf_file.read())
                ucf_file.close()
            else:
                # untar Gzip file
                compressed_dest_file = lfs.open(compressed_dest)
                gzip_file = GzipFile(compressed_dest)
                ucf_path = join(test_path, name)
                ucf_file = lfs.make_file(ucf_path)
                ucf_file.write(gzip_file.read())
                compressed_dest_file.close()
                gzip_file.close()
                ucf_file.close()

    tests = []
    # update test dir name
    test_dir_filenames = lfs.get_names(test_path)
    for filename in test_dir_filenames:
        real_path = join(test_path, filename)
        if lfs.is_file(real_path):
            bytes = lfs.get_size(real_path)
            tests.append((real_path, filename, bytes,
                          get_string_size(bytes)))
    tests.sort(key=lambda x: x[2])
    return tests


###########################################################################
# OUPUT
###########################################################################

def output_init(parsers_name):
    print('-' * 78)
    # 30c | 23c | 23c -> 78c
    print(' %s|%s|%s' % (center('file', 30), center(parser_names[0], 23),
                          center(parser_names[1], 23)))
    print('-' * 78)



def output_result(results, file):
    # file output
    filename, file_size = file
    filename = ljust(filename[:19], 19)
    file_size = get_string_size(file_size)
    file_size = rjust(file_size[:9], 9)
    file_string = '%s  %s' % (filename, file_size)

    # output 1
    parser_name, result = results[0]
    if result is None:
        output1 = center('FAILED',  21)
    else:
        time_spent, memory = result
        memory = get_string_size(memory)
        # time_spent ok already like ___.___ ms or s or mn
        output1 = rjust('%s / %s' % (time_spent, memory), 21)

    # output 2
    parser_name, result = results[1]
    if result is None:
        output2 = center('FAILED',  21)
    else:
        time_spent, memory = result
        memory = get_string_size(memory)
        # time_spent ok already like ___.___ ms or s or mn
        output2 = rjust('%s / %s' % (time_spent, memory), 21)

    print('%s | %s | %s ' % (file_string, output1, output2))


#####################################################################
# MAIN
#####################################################################
parser_scripts = {
    'expat': 'test/bench_xml_expat.py',
    'itools': 'test/bench_xml_itools.py',
    'itools_c': 'test/a.out',
}


if __name__ == '__main__':
    usage = '%prog [OPTIONS]'
    version = 'itools %s' % itools.__version__
    description = ('XML Parser benchmark')
    parser = OptionParser(usage, version=version, description=description)
    parser.add_option(
        '', '--expat-before',
        help='Call Expat parser before itools parser',
        default=False, dest='expat_before', action="store_true")
    parser.add_option(
        '', '--no-gc',
        help='Disable automatic garbage collection.',
        default=False, dest='no_gc', action="store_true")
    parser.add_option(
        '-d', '--directory',
        help=('An optional  directory  to  which  to extract  files.'),
        default='test/bench', dest='test_dir')
    parser.add_option(
        '', '--force-download',
        help='Force the test files download.',
        default=False, dest='force_download', action="store_true")

    options, args = parser.parse_args()
    # Garbage collector
    if options.no_gc is True:
        print('DISABLE GARBAGE COLLECTOR')
        gc.disable()

    # Get test files
    filenames = get_test_filenames(options.test_dir, options.force_download)

    # Order
    if options.expat_before is True:
        parser_names = ['expat', 'itools']
    else:
        parser_names = ['itools', 'expat']
#    parser_names = ['itools_c', 'itools']
    output_init(parser_names)

    # Go
    for real_path, filename, file_bytes, file_size in filenames:
        nb_repeat = get_clock_nb_pass(file_bytes)
        nb_repeat_float = float(nb_repeat)
        nb_repeat = str(nb_repeat)
        test_results = []
        for parser_name in parser_names:
            # Run
            script = parser_scripts[parser_name]
            v0 = vmsize()
            t0 = get_time_spent(mode='both')
            return_code = call([script, real_path, nb_repeat])
            t1 = get_time_spent(mode='both', since=t0)
            v1 = vmsize()
            # Append
            if return_code == 0:
                time_spent = t1 - t0
                memo = v1 - v0
                time_spent = get_string_time(time_spent / nb_repeat_float)
                test_results.append((parser_name, (time_spent, memo)))
            else:
                test_results.append((parser_name, None))
        output_result(test_results, (filename, file_bytes))
    print()

