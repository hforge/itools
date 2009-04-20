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
from optparse import OptionParser
from os import popen
from os.path import islink
from subprocess import call
import sys

# Import from itools
import itools
import itools.gettext
from itools import git
from itools.handlers import ConfigFile, get_handler
from itools.html import XHTMLFile
import itools.stl
from itools import vfs



def get_version():
    # Find out the name of the active branch
    branch_name = git.get_branch_name()
    if branch_name is None:
        return None

    # Look for tags
    tags = git.get_tag_names()
    tags = [ x for x in tags if x.startswith(branch_name) ]

    # And the version name is...
    if tags:
        # Sort so "0.13.10" > "0.13.9"
        key = lambda tag: tuple([ int(x) for x in tag.split('.')])
        tags.sort(key=key)
        # Get the version name
        version_name = tags[-1]
    else:
        version_name = branch_name

    # Get the timestamp
    head = git.get_metadata()
    tag = git.get_metadata(version_name)

    if not tags or tag['tree'] != head['tree']:
        timestamp = head['committer'][1]
        timestamp = timestamp.strftime('%Y%m%d%H%M')
        return '%s-%s' % (version_name, timestamp)

    return version_name



if __name__ == '__main__':
    # The command line parser
    version = 'itools %s' % itools.__version__
    description = ('Builds the package.')
    parser = OptionParser('%prog', version=version, description=description)

    options, args = parser.parse_args()
    if len(args) != 0:
        parser.error('incorrect number of arguments')

    # Try using git facilities
    git_available = git.is_available()
    if not git_available:
        print "Warning: not using git."

    # Read configuration for languages
    config = ConfigFile('setup.conf')
    source_language = config.get_value('source_language', default='en')
    target_languages = config.get_value('target_languages', default='').split()

    # Initialize the manifest file
    manifest = ['MANIFEST', 'version.txt']
    if git_available:
        # Find out the version string
        version = get_version()
        open('version.txt', 'w').write(version)
        print '* Version:', version
        filenames = git.get_filenames()
    else:
        # No git: find out source files
        cmd = ('find -type f|grep -Ev "^./(build|dist)"'
               '|grep -Ev "*.(~|pyc|%s)"' % '|'.join(target_languages))
        filenames = [ x.strip() for x in popen(cmd).readlines() ]
    filenames = [ x for x in filenames if not islink(x) ]
    manifest.extend(filenames)

    # Internationalization
    if vfs.exists('locale'):
        # Build MO files
        print '* Compile message catalogs:',
        sys.stdout.flush()
        for lang in [source_language] + target_languages:
            print lang,
            sys.stdout.flush()
            call([
                'msgfmt', 'locale/%s.po' % lang, '-o', 'locale/%s.mo' % lang])
            # Add to the manifest
            manifest.append('locale/%s.mo' % lang)
        print

        # Load message catalogs
        message_catalogs = {}
        for lang in target_languages:
            path = 'locale/%s.po' % lang
            message_catalogs[lang] = (get_handler(path), vfs.get_mtime(path))

        # Build the templates in the target languages
        cmd = 'find -name "*.x*ml.%s"| grep -Ev "^./(build|dist|skeleton)"'
        lines = popen(cmd % source_language).readlines()
        if lines:
            print '* Build XHTML files',
            sys.stdout.flush()
            # XXX The directory "skeleton" is specific to ikaaro, should not
            # be hardcoded.
            for path in popen(cmd % source_language).readlines():
                # Load the handler
                path = path.strip()
                src_mtime = vfs.get_mtime(path)
                src = XHTMLFile(path)
                done = False
                # Build the translation
                n = path.rfind('.')
                for language in target_languages:
                    po, po_mtime = message_catalogs[language]
                    dst = '%s.%s' % (path[:n], language)
                    # Add to the manifest
                    manifest.append(dst[2:])
                    # Skip the file if it is already up-to-date
                    if vfs.exists(dst):
                        dst_mtime = vfs.get_mtime(dst)
                        if dst_mtime > src_mtime and dst_mtime > po_mtime:
                            continue
                    try:
                        data = src.translate(po)
                    except:
                        print 'Error with file "%s"' % path
                        raise
                    open(dst, 'w').write(data)
                    done = True
                # Done
                if done is True:
                    sys.stdout.write('*')
                else:
                    sys.stdout.write('.')
                sys.stdout.flush()
            print

    # Build the manifest file
    manifest.sort()
    lines = [ x + '\n' for x in manifest ]
    open('MANIFEST', 'w').write(''.join(lines))
    print '* Build MANIFEST file (list of files to install)'
