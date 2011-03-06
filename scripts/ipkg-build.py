#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
from re import compile
from optparse import OptionParser
from os.path import islink
from subprocess import call
from sys import exc_info, stdout
from traceback import print_exception

# Import from itools
import itools
import itools.gettext
from itools.git import WorkTree
from itools.handlers import ro_database
from itools.html import XHTMLFile
import itools.pdf
from itools.pkg import get_config, get_files, get_manifest, make_version
import itools.stl
from itools.fs import lfs


def build():
    worktree = WorkTree('.')
    # Try using git facilities
    git_available = worktree.is_available()
    if not git_available:
        print "Warning: not using git."

    # Read configuration for languages
    config = get_config()
    source_language = config.get_value('source_language', default='en')
    target_languages = config.get_value('target_languages')

    # (1) Initialize the manifest file
    manifest = [ x for x in get_manifest() if not islink(x) ]
    manifest.append('MANIFEST')
    # Find out the version string
    if git_available:
        version = make_version()
        open('version.txt', 'w').write(version)
        print '* Version:', version
        manifest.append('version.txt')

    # (2) Internationalization
    bad_templates = []
    if lfs.exists('locale'):
        # Build MO files
        print '* Compile message catalogs:',
        stdout.flush()
        for lang in (source_language,) + target_languages:
            print lang,
            stdout.flush()
            call([
                'msgfmt', 'locale/%s.po' % lang, '-o', 'locale/%s.mo' % lang])
            # Add to the manifest
            manifest.append('locale/%s.mo' % lang)
        print

        # Load message catalogs
        message_catalogs = {}
        for lang in target_languages:
            path = 'locale/%s.po' % lang
            handler = ro_database.get_handler(path)
            message_catalogs[lang] = (handler, lfs.get_mtime(path))

        # Build the templates in the target languages
        good_files = compile('.*\\.x.*ml.%s$' % source_language)
        exclude = frozenset(['.git', 'build', 'docs', 'dist'])
        lines = get_files(exclude, filter=lambda x: good_files.match(x))
        lines = list(lines)
        if lines:
            print '* Build XHTML files',
            stdout.flush()
            for path in lines:
                # Load the handler
                src_mtime = lfs.get_mtime(path)
                src = ro_database.get_handler(path, XHTMLFile)
                done = False
                # Build the translation
                n = path.rfind('.')
                error = False
                for language in target_languages:
                    po, po_mtime = message_catalogs[language]
                    dst = '%s.%s' % (path[:n], language)
                    # Add to the manifest
                    manifest.append(dst)
                    # Skip the file if it is already up-to-date
                    if lfs.exists(dst):
                        dst_mtime = lfs.get_mtime(dst)
                        if dst_mtime > src_mtime and dst_mtime > po_mtime:
                            continue
                    try:
                        data = src.translate(po)
                    except StandardError:
                        error = True
                        bad_templates.append((path, exc_info()))
                    else:
                        open(dst, 'w').write(data)
                        done = True
                # Done
                if error is True:
                    stdout.write('E')
                elif done is True:
                    stdout.write('*')
                else:
                    stdout.write('.')
                stdout.flush()
            print

    # (3) Build the manifest file
    manifest.sort()
    lines = [ x + '\n' for x in manifest ]
    open('MANIFEST', 'w').write(''.join(lines))
    print '* Build MANIFEST file (list of files to install)'

    # (4) Show errors
    if bad_templates:
        print
        print '***********************************************************'
        print 'The following templates could not be translated'
        print '***********************************************************'
        for (path, (type, value, traceback)) in bad_templates:
            print
            print path
            print_exception(type, value, traceback)




if __name__ == '__main__':
    # The command line parser
    version = 'itools %s' % itools.__version__
    description = ('Builds the package.')
    parser = OptionParser('%prog', version=version, description=description)
    parser.add_option('--profile',
        help="print profile information to the given file")

    options, args = parser.parse_args()
    if len(args) != 0:
        parser.error('incorrect number of arguments')

    if options.profile is not None:
        from cProfile import runctx
        runctx("build()", globals(), locals(), options.profile)
    else:
        build()
