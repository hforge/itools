
Itools is a Python package that encapsulates several Python tools
developed by the Itaapy company and other developers. The provided
tools are:

 * itools.uri -- an API to manage URIs, to identify and locate resources;

 * itools.resources -- an abstraction layer over resources that let to
   manage them with a consistent API, independently of where they are stored;

 * itools.handlers -- resource handlers, they are non persistent classes
   that add specific semantic to resources, for example there are handlers
   for file formats like XML, CSV, PO, etc..

 * itools.i18n -- tools for language negotiation and text segmentation.

 * itools.workflow -- represent workflows as automatons, objects can move
   from one state to another through transitions, classes can add specific
   semantics to states and transitions

 * itools.zope -- miscellaneous utilities for Zope


Install
-------

Unpack the package and run "python setup.py install", be sure to have
the right permissions, maybe you will need to run the command as root.


Download
--------

The releases and the CVS can be reached from SourceForge:

  http://sourceforge.net/projects/lleu


Author and license
------------------

Copyright 2002-2004  J. David Ibáñez <jdavid@itaapy.com>
          2002 Thilo Ernst <Thilo.Ernst@dlr.de>

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA