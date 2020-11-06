# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2009 Hervé Cauwelier <herve@oursours.net>
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
from __future__ import print_function
import sys
from distutils.core import Extension
from distutils.core import setup
from os.path import join as join_path
from pip._internal.req import parse_requirements
from sys import stderr
from subprocess import Popen, PIPE


def get_pipe(command, cwd=None):
    """Wrapper around 'subprocess.Popen'
    """
    popen = Popen(command, stdout=PIPE, stderr=PIPE, cwd=cwd)
    stdoutdata, stderrdata = popen.communicate()
    if popen.returncode != 0:
        raise EnvironmentError(popen.returncode, stderrdata)
    return stdoutdata


def get_compile_flags(command):
    include_dirs = []
    extra_compile_args = []
    library_dirs = []
    libraries = []

    if isinstance(command, str):
        command = command.split()
    data = get_pipe(command)

    for line in data.splitlines():
        for token in line.split():
            flag, value = token[:2], token[2:]
            if flag == '-I':
                include_dirs.append(value)
            elif flag == '-f':
                extra_compile_args.append(token)
            elif flag == '-L':
                library_dirs.append(value)
            elif flag == '-l':
                libraries.append(value)

    return {'include_dirs': include_dirs,
            'extra_compile_args': extra_compile_args,
            'library_dirs': library_dirs,
            'libraries': libraries}


def generate_mo_files(po_file_names):
    """
    Generate mo files from po files located on /itools/locale/
    :param po_file_names: An array of po files location
    :return: An array of mo files location
    """
    mo_files = []
    for po_file in po_file_names:
        # Compute mo file name
        mo_file = po_file.replace('.po', '.mo')
        # Generate mo file
        try:
            Popen(['msgfmt', po_file, '-o', mo_file])
        except OSError:
            # Check msgfmt is properly installed
            print("[ERROR] 'msgfmt' not found, aborting...", file=stderr)
            return []
        mo_files.append(mo_file)
    return mo_files


if __name__ == '__main__':
    itools_is_available = False
    try:
        from itools.core import get_abspath
        from itools.pkg import setup as itools_setup
        itools_is_available = True
        print('[OK] itools is available')
    except ImportError:
        print('[Warning] itools is not available')
        pass
    ext_modules = []

    filenames = [x.strip() for x in open('MANIFEST').readlines() ]
    if not itools_is_available:
        # In case itools is not yet install, build won't work
        # thus we need to make sure mo files will be generated
        po_files = [x for x in filenames if x.endswith('.po') and not x.startswith('docs/')]
        # Generate mo files
        mo_files = generate_mo_files(po_files)
        # Append mo_files to filenames
        filenames.extend(mo_files)

    # XML Parser
    try:
        flags = get_compile_flags('pkg-config --cflags --libs glib-2.0')
    except OSError:
        print("[ERROR] 'pkg-config' not found, aborting...", file=stderr)
        raise
    except EnvironmentError:
        err = '[ERROR] Glib 2.0 library or headers not found, aborting...'
        print(err, file=stderr)
        raise
    else:
        sources = [
            'itools/xml/parser.c', 'itools/xml/doctype.c', 'itools/xml/arp.c',
            'itools/xml/pyparser.c']
        extension = Extension('itools.xml.parser', sources, **flags)
        ext_modules.append(extension)

    # PDF indexation
    try:
        flags = get_compile_flags(
            'pkg-config --cflags --libs "poppler >= 0.20.0" fontconfig')
    except EnvironmentError:
        err = "[WARNING] poppler headers not found, PDF indexation won't work"
        print(err, file=stderr)
    else:
        sources = ['itools/pdf/pdftotext.cc']
        extension = Extension('itools.pdf.pdftotext', sources, **flags)
        ext_modules.append(extension)

    # DOC indexation
    try:
        flags = get_compile_flags('wv2-config --cflags --libs')
    except EnvironmentError:
        err = "[WARNING] wv2 not found, DOC indexation won't work"
        print(err, file=stderr)
    else:
        sources = ['itools/office/doctotext.cc']
        extension = Extension('itools.office.doctotext', sources, **flags)
        ext_modules.append(extension)

    # On python 3, no extension is available yet FIXME 2to3
    if sys.version_info[0] == 3:
        ext_modules = []

    # Ok
    if itools_is_available:
        itools_setup(get_abspath(''), ext_modules=ext_modules)
        exit(0)

    # Ok
    description = """The itools library offers a collection of packages covering a wide
     range of capabilities.  Including support for many file formats (XML,
     CSV, HTML, etc.), a virtual file system (itools.fs), the simple
     template language (STL), an index and search engine, and much more."""
    classifiers = [
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: GNU General Public License (GPL)',
      'Programming Language :: Python',
      'Topic :: Internet',
      'Topic :: Internet :: WWW/HTTP',
      'Topic :: Software Development',
      'Topic :: Software Development :: Internationalization',
      'Topic :: Software Development :: Libraries',
      'Topic :: Software Development :: Libraries :: Python Modules',
      'Topic :: Software Development :: Localization',
      'Topic :: Text Processing',
      'Topic :: Text Processing :: Markup',
      'Topic :: Text Processing :: Markup :: XML"',
    ]
    packages = [
        "itools",
        "itools.core",
        "itools.csv",
        "itools.database",
        "itools.database.backends",
        "itools.datatypes",
        "itools.fs",
        "itools.gettext",
        "itools.handlers",
        "itools.html",
        "itools.i18n",
        "itools.ical",
        "itools.log",
        "itools.loop",
        "itools.odf",
        "itools.office",
        "itools.pdf",
        "itools.pkg",
        "itools.python",
        "itools.relaxng",
        "itools.rss",
        "itools.srx",
        "itools.stl",
        "itools.tmx",
        "itools.uri",
        "itools.validators",
        "itools.web",
        "itools.workflow",
        "itools.xliff",
        "itools.xml",
        "itools.xmlfile"]
    scripts =  [
      "scripts/idb-inspect.py",
      "scripts/igettext-build.py",
      "scripts/igettext-extract.py",
      "scripts/igettext-merge.py",
      "scripts/ipkg-build.py",
      "scripts/ipkg-docs.py",
      "scripts/ipkg-quality.py",
      "scripts/ipkg-update-locale.py"]
    # FIXME 2to3
    if sys.version_info[0] == 3:
        install_requires = []
    else:
        install_requires = parse_requirements('requirements.txt', session='xxx')
        install_requires = [str(ir.requirement) for ir in install_requires]
    # The data files
    package_data = {'itools': []}
    filenames = [ x for x in filenames if not x.endswith('.py') ]
    for line in filenames:
        if not line.startswith('itools/'):
            continue
        path = line.split('/')
        subpackage = 'itools.%s' % (path[1])
        if subpackage in packages:
            files = package_data.setdefault(subpackage, [])
            files.append(join_path(*path[2:]))
        else:
            package_data['itools'].append(join_path(*path[1:]))
    setup(name="itools",
          version="0.78.0",
          # Metadata
          author="J. David Ibáñez",
          author_email="jdavid.ibp@gmail.com" ,
          license="GNU General Public License (GPL)",
          url="http://www.hforge.org/itools",
          description=description,
          long_description=None,
          classifiers = classifiers,
          install_requires=install_requires,
          # Packages
          packages=packages,
          package_data=package_data,
          # Scripts
          scripts=scripts,
          # C extensions
          ext_modules=ext_modules)
