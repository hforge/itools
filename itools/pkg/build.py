# -*- coding: UTF-8 -*-
# Copyright (C) 2006, 2010 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2006-2007, 2009-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2009 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2016 Sylvain Taverne <taverne.sylvain@gmail.com>
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


# Import from standard library
from os.path import islink
from subprocess import Popen

# Import from itools
from itools.fs import lfs
from itools.handlers import ro_database

# Import from here
from git import open_worktree


def get_manifest():
    worktree = open_worktree('.')
    exclude = frozenset(['.gitignore'])
    return [ x for x in worktree.get_filenames() if x not in exclude ]


def make(worktree, rules, manifest):
    for source in worktree.get_filenames():
        # Exclude
        if 'docs/' in source:
            continue
        # Apply rules
        for source_ext, target_ext, f in rules:
            if source.endswith(source_ext):
                target = source[:-len(source_ext)] + target_ext
                if not lfs.exists(target) or \
                   lfs.get_mtime(source) > lfs.get_mtime(target):
                    f(source, target)     # 1. Compile
                    manifest.add(target)  # 2. Update manifest
                    print target          # 3. Print


# PO => MO
def po2mo(source, target):
    Popen(['msgfmt', source, '-o', target])


# Translate templates
def make_template(source, target):
    # Import some packages so we can compile templates
    from itools.html import XHTMLFile
    import itools.gettext
    import itools.stl
    # Get file
    source_handler = ro_database.get_handler(source, XHTMLFile)
    language = target.rsplit('.', 1)[1]
    po = ro_database.get_handler('locale/%s.po' % language)
    data = source_handler.translate(po)
    with open(target, 'w') as f:
        f.write(data)



# SASS: CSS preprocessor
def scss2css(source, target):
    Popen(['scss', source, target])



def make_version(worktree):
    """This function finds out the version number from the source, this will
    be written to the 'version.txt' file, which will be read once the software
    is installed to get the version number.
    """
    # The name of the active branch
    branch = worktree.get_branch_name()
    if branch is None:
        return None

    # The tag
    description = worktree.git_describe()

    # The version name
    if description:
        tag, n, commit = description
        if tag.startswith(branch):
            version = tag
        else:
            version = '%s-%s' % (branch, tag)
        # Exact match
        if n == 0:
            return version
    else:
        version = branch

    # Get the timestamp
    head = worktree.get_metadata()
    timestamp = head['committer_date']
    timestamp = timestamp.strftime('%Y%m%d%H%M')
    return '%s-%s' % (version, timestamp)


def build(config):
    package_root = config.get_value('package_root')
    # Get git worktree
    worktree = open_worktree('.')
    # Initialize the manifest file
    manifest = set([ x for x in get_manifest() if not islink(x) ])
    manifest.add('MANIFEST')
    # Find out the version string
    version = make_version(worktree)
    # Write version
    if package_root == '.':
        version_txt = 'version.txt'
    else:
        version_txt = package_root + '/version.txt'
    open(version_txt, 'w').write(version)
    print '* Version:', version
    manifest.add(version_txt)
    # (3) Rules
    rules = [
        ('.po', '.mo', po2mo),
        ('.scss', '.css', scss2css)]
    # Templates
    src_lang = config.get_value('source_language', default='en')
    for dst_lang in config.get_value('target_languages'):
        rules.append(
            ('.xml.%s' % src_lang, '.xml.%s' % dst_lang, make_template))
        rules.append(
            ('.xhtml.%s' % src_lang, '.xhtml.%s' % dst_lang, make_template))
    # (4) Make
    make(worktree, rules, manifest)
    # (5) Write the manifest
    lines = [ x + '\n' for x in sorted(manifest) ]
    open('MANIFEST', 'w').write(''.join(lines))
    print '* Build MANIFEST file (list of files to install)'
    return version
