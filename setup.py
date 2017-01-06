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
from distutils.core import Extension
from distutils.core import setup
from os.path import join as join_path
from pip.download import PipSession
from pip.req import parse_requirements
from sys import stderr
from subprocess import Popen, PIPE


def get_pipe(command, cwd=None):
    """Wrapper around 'subprocess.Popen'
    """
    popen = Popen(command, stdout=PIPE, stderr=PIPE, cwd=cwd)
    stdoutdata, stderrdata = popen.communicate()
    if popen.returncode != 0:
        raise EnvironmentError, (popen.returncode, stderrdata)
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


if __name__ == '__main__':
    ext_modules = []

    # XML Parser
    try:
        flags = get_compile_flags('pkg-config --cflags --libs glib-2.0')
    except OSError:
        print >> stderr, "[ERROR] 'pkg-config' not found, aborting..."
        raise
    except EnvironmentError:
        err = '[ERROR] Glib 2.0 library or headers not found, aborting...'
        print >> stderr, err
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
            'pkg-config --cflags --atleast-version=0.20.0 --libs poppler fontconfig')
    except EnvironmentError:
        err = "[WARNING] poppler headers not found, PDF indexation won't work"
        print >> stderr, err
    else:
        sources = ['itools/pdf/pdftotext.cc']
        extension = Extension('itools.pdf.pdftotext', sources, **flags)
        ext_modules.append(extension)

    # DOC indexation
    try:
        flags = get_compile_flags('wv2-config --cflags --libs')
    except EnvironmentError:
        err = "[WARNING] wv2 not found, DOC indexation won't work"
        print >> stderr, err
    else:
        sources = ['itools/office/doctotext.cc']
        extension = Extension('itools.office.doctotext', sources, **flags)
        ext_modules.append(extension)

    # libsoup wrapper
    line = 'pkg-config --cflags --libs gthread-2.0 libsoup-2.4'
    try:
        flags = get_compile_flags(line)
    except EnvironmentError:
        err = "[WARNING] libsoup not found, itools.web won't work"
        print >> stderr, err
    else:
        for include in flags['include_dirs']:
            if include.endswith('/libsoup-2.4'):
                flags['include_dirs'].append('%s/libsoup' % include)
                break
        sources = ['itools/web/soup.c']
        extension = Extension('itools.web.soup', sources, **flags)
        ext_modules.append(extension)

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
      "scripts/iodf-greek.py",
      "scripts/ipkg-docs.py",
      "scripts/ipkg-quality.py",
      "scripts/ipkg-update-locale.py"]
    install_requires = parse_requirements(
        'requirements.txt', session=PipSession())
    install_requires = [str(ir.req) for ir in install_requires]
    # The data files
    package_data = {'itools': []}
    filenames = [ x.strip() for x in open('MANIFEST').readlines() ]
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
          version="0.75",
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
