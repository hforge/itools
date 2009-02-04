
itools is a Python library, it groups a number of packages into a single
meta-package for easier development and deployment.

The packages included are:

  itools.abnf             itools.ical             itools.tmx
  itools.core             itools.odf              itools.uri
  itools.csv              itools.pdf              itools.vfs
  itools.datatypes        itools.pkg              itools.web
  itools.gettext          itools.python           itools.workflow
  itools.git              itools.relaxng          itools.xapian
  itools.handlers         itools.rest             itools.xliff
  itools.html             itools.rss              itools.xml
  itools.http             itools.srx              itools.xmlfile
  itools.i18n             itools.stl

The scripts included are:

  igettext-build.py       ipkg-info.py            isetup-build.py
  igettext-extract.py     ipkg-install.py         isetup-copyright.py
  igettext-merge.py       ipkg-register.py        isetup-quality.py
  ipkg-cache-list.py      ipkg-release.py         isetup-update-locale.py


Requirements
=============

Software    Version   Required by     Home
---------   -------   -------------   ----------------------------------------
Python        2.6.1   itools          http://www.python.org/
glib           2.16   itools.vfs      http://www.gtk.org/
pygobject      2.16   itools.vfs      http://www.pygtk.org/
reportlab       2.2   itools.pdf      http://www.reportlab.org/
xapian        1.0.8   itools.xapian   http://www.xapian.org/
pywin32         212   (Windows)       http://sourceforge.net/projects/pywin32/


Install
=============

If you are reading this instructions you probably have already unpacked
the itools tarball with the command line:

  $ tar xzf itools-X.Y.Z.tar.gz

And changed the working directory this way:

  $ cd itools-X.Y.Z

So now to install itools you just need to type this:

  $ python setup.py install


Unit Tests
=============

To run the unit tests just type:

  $ cd test
  $ python test.py

If there are errors, please report either to the issue tracker or to
the mailing list:

  - http://bugs.hforge.org/
  - http://www.hforge.org/community


Documentation
=============

The documentation is distributed as a separate package, itools-docs.
The PDF file can be downloaded from http://www.hforge.org/itools


Resources
=============

Home
http://www.hforge.org/itools

Mailing list
http://www.hforge.org/community/
http://archives.hforge.org/index.cgi?list=itools

Bug Tracker
http://bugs.hforge.org


Copyright
=============

Copyright (C) 2002-2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
Copyright (C) 2005-2009 Luis Arturo Belmar-Letelier <luis@itaapy.com>
Copyright (C) 2005-2009 Hervé Cauwelier <herve@itaapy.com>
Copyright (C) 2005-2009 Nicolas Deram <nicolas@itaapy.com>

And others. Check the CREDITS file for complete list.


License
=============

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

