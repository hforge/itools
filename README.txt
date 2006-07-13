
itools is a Python library, it groups a number of packages into a single
meta-package for easier development and deployment.

The packages included are:

  itools.catalog        itools.http             itools.tmx
  itools.cms            itools.i18n             itools.uri
  itools.csv            itools.ical             itools.web
  itools.datatypes      itools.resources        itools.workflow
  itools.gettext        itools.rss              itools.xhtml
  itools.handlers       itools.schemas          itools.xliff
  itools.html           itools.stl              itools.xml

The scripts included are:

  icms-init             icms-update             igraph.py
  icms-restore          igettext-build          isetup-build
  icms-start            igettext-extract        isetup-test
  icms-stop             igettext-merge          isetup-update-locale


Requirements
------------

itools requires Python 2.4 or later.

The PIL Python package is recommended, itools.cms will use it if it is
installed.

The commands rsync and tidy are required by itools.cms; the commands
xlhtml, pdftotext, catdoc, ppthtml, iconv, links, unzip, pdftohtml
and wvHtml are recommended, itools.cms will use them if installed to
index documents.


Install
-------

Unpack the package and run "python setup.py install", be sure to have
the right permissions, maybe you will need to run the command as root.

To deploy an instance of itools.cms check the documentation about itools
(see http://www.ikaaro.org/itools). To install an itools.cms instance
behind Apache, with virtual hosting the rewrite rule to use will look like:

  <VirtualHost *:80>
    ServerName example
    RewriteEngine On
    RewriteRule ^/(.*) http://localhost:8080/example/$1 [P]
    RequestHeader set X-Base-Path example
  </VirtualHost>


Documentation
-------------

The documentation is distributed as a separate package, itools-docs.
The PDF file can be downloaded from http://www.ikaaro.org/itools


Resources
---------

Home
http://www.ikaaro.org/itools

Mailing list
http://in-girum.net/mailman/listinfo/ikaaro

Bug Tracker
http://bugs.ikaaro.org


Copyright
----------

Copyright 2002-2005  J. David Ibáñez <jdavid@itaapy.com>

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
