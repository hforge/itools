# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA



# Import Python modules
from distutils.command import build_py
from distutils.core import setup
from glob import glob
import os
import string



class build_py(build_py.build_py):
    """
    Provides a version of the Distutils 'build_py' command that knows about
    DTML and text files.

    Copied from quixote.qx_distutils.py

    This bites -- way too much code had to be copied from
    distutils/command/build.py just to add an extra file extension!
    """

    def find_package_modules(self, package, package_dir):
        self.check_package(package, package_dir)
        module_files = (glob(os.path.join(package_dir, "*.py")) +
                        glob(os.path.join(package_dir, "*.dtml")) +
                        glob(os.path.join(package_dir, "*.tex")) +
                        glob(os.path.join(package_dir, "*.txt")))
        modules = []
        setup_script = os.path.abspath(self.distribution.script_name)

        for f in module_files:
            abs_f = os.path.abspath(f)
            if abs_f != setup_script:
                module = os.path.splitext(os.path.basename(f))[0]
                modules.append((package, module, f))
            else:
                self.debug_print("excluding %s" % setup_script)
        return modules


    def build_module(self, module, module_file, package):
        if isinstance(package, str):
            package = package.split('.')
        elif not isinstance(package, (list, tuple)):
            raise TypeError, \
                  "'package' must be a string (dot-separated), list, or tuple"

        # Now put the module source file into the "build" area -- this is
        # easy, we just copy it somewhere under self.build_lib (the build
        # directory for Python source).
        outfile = self.get_module_outfile(self.build_lib, package, module)
        if module_file.endswith(".dtml"): # XXX hack for DTML
            outfile = outfile[0:outfile.rfind('.')] + ".dtml"
        elif module_file.endswith(".txt"): # XXX hack for TXT
            outfile = outfile[0:outfile.rfind('.')] + ".txt"
        elif module_file.endswith(".tex"): # XXX hack for TEX
            outfile = outfile[0:outfile.rfind('.')] + ".tex"
        dir = os.path.dirname(outfile)
        self.mkpath(dir)
        return self.copy_file(module_file, outfile, preserve_mode=0)



# XXX itools.zope.zmi shouldn't be a Python package, but this is the
# quickest workaround I found to install this directory.
description = """Itools is a Python package that encapsulates several Python
tools developed by the Itaapy company and other developers. The provided
tools are:

 * itools.uri -- an API to manage URIs, to identify and locate resources.

 * itools.resources -- an abstraction layer over resources that let to
   manage them with a consistent API, independently of where they are stored.

 * itools.handlers -- resource handlers infrastructure (resource
   handlers are non persistent classes that add specific semantics to
   resources). This package also includes several handlers out of the
   box.

 * itools.xml -- XML infrastructure, includes resource handlers for XML,
   XHTML and HTML documents. Plus the Simple Template Language.

 * itools.i18n -- tools for language negotiation and text segmentation.

 * itools.workflow -- represent workflows as automatons, objects can move
   from one state to another through transitions, classes can add specific
   semantics to states and transitions.

 * itools.catalog -- An Index & Search engine.
"""

setup(name = "itools",
      version = "0.4.4",
      author = "J. David Ibáñez",
      author_email = "jdavid@itaapy.com",
      license = "GNU Lesser General Public License",
      url = "http://sf.net/projects/lleu",
      description="Misc. tools: uri, resources, handlers, i18n, workflow",
      long_description=description,
      package_dir = {'itools': ''},
      packages = ['itools', 'itools.catalog', 'itools.handlers', 'itools.i18n',
                  'itools.lucene', 'itools.resources', 'itools.workflow',
                  'itools.xml', 'itools.zope'],
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
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
                   'Topic :: Text Processing :: Markup :: XML'],
##      data_files = [('zope', ['zope/localroles.dtml'])],
      scripts = ['i18n/igettext.py'],
      cmdclass = {'build_py': build_py})
