
itools is a Python library, it groups a number of packages into a single
meta-package for easier development and deployment.

The packages included are:

  itools.catalog        itools.i18n             itools.vfs
  itools.cms            itools.ical             itools.web
  itools.csv            itools.pdf              itools.workflow
  itools.datatypes      itools.rss              itools.xhtml
  itools.gettext        itools.schemas          itools.xliff
  itools.handlers       itools.stl              itools.xml
  itools.html           itools.tmx
  itools.http           itools.uri

The scripts included are:

  icms-init             icms-update             isetup-build
  icms-restore          igettext-build          isetup-update-locale
  icms-start            igettext-extract
  icms-stop             igettext-merge



Requirements
------------

itools requires Python 2.5 or later.

For itools.cms to work the package "tidy" [1] must be installed. While not
strictly necessary it is also recommended to have PIL [2] and docutils [3]
installed.

Apart from the Python packages listed above, itoools.cms requires the
command rsync. And the commands xlhtml, ppthtml, pdftohtml, wvHtml and
unrtf are needed to index some types of documents.

[1] http://utidylib.berlios.de/
[2] http://www.pythonware.com/products/pil/
[3] http://docutils.sourceforge.net/



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

 - Luis Belmar Letelier <luis@itaapy.com>
 - Hervé Cauwelier <herve@oursours.net>
 - Nicolas Deram <nderam@gmail.com>
 - Thilo Ernst <Thilo.Ernst@dlr.de>
 - Alexandre Fernandez <>
 - Thierry Fromon <from.t@free.fr>
 - J. David Ibáñez <jdavid@itaapy.com>
 - Piotr Macuk <piotr@macuk.pl>
 - Cedric Moliard <>
 - Nicolas Oyez <noyez@gmail.com>

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
