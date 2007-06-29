
itools is a Python library, it groups a number of packages into a single
meta-package for easier development and deployment.

The packages included are:

  itools.catalog        itools.i18n             itools.tmx
  itools.cms            itools.ical             itools.uri
  itools.csv            itools.odf              itools.vfs
  itools.datatypes      itools.pdf              itools.web
  itools.gettext        itools.rest             itools.workflow
  itools.handlers       itools.rss              itools.xhtml
  itools.html           itools.schemas          itools.xliff
  itools.http           itools.stl              itools.xml

The scripts included are:

  icatalog-inspect      icms-update             isetup-build
  icms-init             icms-update-catalog     isetup-doc
  icms-restore          igettext-build          isetup-update-locale
  icms-start            igettext-extract
  icms-stop             igettext-merge


Requirements
------------

Python 2.5 or later is required.

For the implementation of RML (itools.pdf) to work the package reportlab [1]
must be installed.

For itools.cms to work the package "tidy" [2] must be installed. While not
strictly necessary it is also recommended to have PIL [3] and docutils [4]
installed.

Apart from the Python packages listed above, itools.cms requires the commands
xlhtml, ppthtml, pdftotext, wvText and unrtf to index some types of documents.

[1] http://www.reportlab.org/
[2] http://utidylib.berlios.de/
[3] http://www.pythonware.com/products/pil/
[4] http://docutils.sourceforge.net/



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



Deploy itools.cms: Virtual Hosting
----------------------------------

To deploy an instance of itools.cms check the documentation about itools
(see http://www.ikaaro.org/itools). To install an itools.cms instance
behind Apache, with virtual hosting the rewrite rule to use will look like:

  <VirtualHost *:80>
    ServerName example
    RewriteEngine On
    RewriteRule ^/(.*) http://localhost:8080/example/$1 [P]
    RequestHeader set X-Base-Path example
  </VirtualHost>



Resources
---------

Home
http://www.ikaaro.org/itools

Mailing list
http://mail.ikaaro.org/mailman/listinfo/itools

Bug Tracker
http://bugs.ikaaro.org


Copyright
----------

Copyright 2002-2007  J. David Ibáñez <jdavid@itaapy.com>

And:

 - Luis Belmar-Letelier <luis@itaapy.com>
 - Hervé Cauwelier <herve@itaapy.com>
 - Nicolas Deram <nderam@itaapy.com>
 - Thilo Ernst <Thilo.Ernst@dlr.de>
 - Thierry Fromon <from.t@free.fr>
 - Piotr Macuk <piotr@macuk.pl>
 - Henry Obein <henry@itaapy.com>
 - Nicolas Oyez <noyez@gmail.com>
 - Sylvain Taverne <sylvain@itaapy.com>

Includes parts of Epoz 2.0.2. Epoz is copyrighted by Maik Jablonski and
licensed under the Zope Public License (ZPL) version 2.1.

Most icons used are copyrighted by the Tango Desktop Project, and licensed
under the Creative Commons Attribution Share-Alike license, including the
modifications to them. (http://creativecommons.org/licenses/by-sa/2.5/)


License
-------

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
