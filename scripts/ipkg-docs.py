#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from os import chdir
from subprocess import call

# Import from itools
import itools
from itools.core import get_pipe
from itools.fs import lfs


def run(command):
    # Format command
    if type(command) is str:
        command_str = command
        command = command.split()
    else:
        command_str = ' '.join(command)
    # Print
    print command_str
    # Call
    return call(command)


sphinx = (
    'sphinx-build -b {mode} -d _build/doctrees -D latex_paper_size=a4 . '
    '_build/{mode}')

converters = {
    ('png', 'png'): 'cp {source} {target}',
    ('jpg', 'png'): 'convert {source} {target}',
    ('svg', 'png'): 'inkscape -z {source} -e {target}',
    ('dot', 'png'): 'dot -Tpng {source} -o {target}',
    ('png', 'eps'): 'convert {source} -compress jpeg eps2:{target}',
    ('jpg', 'eps'):
        'convert -units PixelsPerInch -density 72 {source} eps2:{target}',
    ('svg', 'eps'): 'inkscape -z {source} -E {target}',
    ('fig', 'eps'): 'fig2dev -L eps {source} {target}',
    ('dot', 'eps'): 'dot -Tps {source} -o {target}'}


def make_figures(format):
    source_base = 'figures-src'
    target_base = 'figures'

    docs = lfs.open('docs')
    if not docs.exists(source_base):
        return

    if not docs.exists(target_base):
        docs.make_folder(target_base)

    for name in docs.get_names(source_base):
        source = '%s/%s' % (source_base, name)
        mtime = docs.get_mtime(source)
        name, extension = name.rsplit('.')
        target = '%s/%s.%s' % (target_base, name, format)
        if docs.exists(target) and docs.get_mtime(target) > mtime:
            continue
        command = converters.get((extension, format))
        if command:
            command = command.format(source=source, target=target)
            run(command)


def make_html():
    make_figures('png')
    # HTML
    command = sphinx.format(mode='html')
    print run(command)
    # Ok
    print 'The HTML pages are in docs/_build/html'


def make_pdf():
    # Figures
    make_figures('eps')
    # Latex
    command = sphinx.format(mode='latex')
    print run(command)
    # PDF
    chdir('_build/latex')
    print run('make all-pdf')
    print 'The PDF is available in docs/_build/latex'


def make_release():
    # Make HTML
    make_html()

    # Make the tarball
    chdir('_build/html')
    call('tar cpf %s.tar *' % pkgname, shell=True)
    print 'The tarball is available in docs/_build/html/%s.tar' % pkgname


if __name__ == '__main__':
    # The command line parser
    usage = '%prog [html|pdf|release]'
    version = 'itools %s' % itools.__version__
    description = ('Make the documentation, default mode is html.')
    parser = OptionParser(usage, version=version, description=description)

    options, args = parser.parse_args()
    if len(args) > 1:
        parser.error('incorrect number of arguments')

    mode = args[0] if args else 'html'

    # Find out the package name & version (for the release mode)
    try:
        pkgname = get_pipe(['python', 'setup.py', '--fullname']).rstrip()
    except EnvironmentError:
        pkgname = 'noname-noversion'

    # Go
    chdir('docs')
    if mode == 'html':
        make_html()
    elif mode == 'pdf':
        make_pdf()
    elif mode == 'release':
        make_release()
    else:
        parser.error('unkwnon "%s" mode' % mode)
