
itools is a Python library, it groups a number of packages into a single
meta-package for easier development and deployment.

The packages included are:

  itools.abnf             itools.i18n             itools.uri
  itools.csv              itools.ical             itools.vfs
  itools.datatypes        itools.odf              itools.web
  itools.gettext          itools.pdf              itools.workflow
  itools.git              itools.rest             itools.xapian
  itools.handlers         itools.rss              itools.xliff
  itools.html             itools.stl              itools.xml
  itools.http             itools.tmx

The scripts included are:

  igettext-build.py       isetup-quality.py       isetup-update-locale.py
  igettext-extract.py     isetup-build.py
  igettext-merge.py       isetup-copyright.py


Requirements
------------

Python 2.5 or later is required.  The GLib [1] library version 2.12 or
later is required.

For the implementation of RML (itools.pdf) to work the package reportlab [2]
must be installed.

For itools.xapian, you need the latest xapian-core and xapian-bindings
packages [3].


[1] http://www.gtk.org/
[2] http://www.reportlab.org/
[3] http://www.xapian.org/


Install
-------

If you are reading this instructions you probably have already unpacked
the itools tarball with the command line:
    
  $ tar xzf itools-X.Y.Z.tar.gz

And changed the working directory this way:
    
  $ cd itools-X.Y.Z

So now to install itools you just need to type this:

  $ python setup.py install



Unit Tests
----------

To run the unit tests just type:
    
  $ cd test
  $ python test.py

If there are errors, please report either to the issue tracker or to
the mailing list:

  - http://bugs.ikaaro.org
  - http://mail.ikaaro.org/mailman/listinfo/itools



Documentation
-------------

The documentation is distributed as a separate package, itools-docs.
The PDF file can be downloaded from http://www.ikaaro.org/itools



Resources
---------

Home
http://www.ikaaro.org/itools

Mailing list
http://www.ikaaro.org/community/
http://archives.ikaaro.org/index.cgi?list=itools

Bug Tracker
http://bugs.ikaaro.org


Copyright
---------

Copyright (C) 2002-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
Copyright (C) 2005-2008 Luis Arturo Belmar-Letelier <luis@itaapy.com>
Copyright (C) 2005-2008 Hervé Cauwelier <herve@itaapy.com>
Copyright (C) 2005-2008 Nicolas Deram <nicolas@itaapy.com>

And others. Check the CREDITS file for complete list.


License
-------

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

