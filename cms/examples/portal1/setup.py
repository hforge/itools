# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

# Import from the Standard Library
from distutils.core import setup
from distutils.command.build_py import build_py
from os.path import join



class build_py_fixed(build_py):
    """http://sourceforge.net/tracker/index.php?func=detail&aid=1183712&group_id=5470&atid=305470"""
    def get_data_files(self):
        """Generate list of '(package,src_dir,build_dir,filenames)' tuples"""
        data = []
        if not self.packages:
            return data
        for package in self.packages:
            # Locate package source directory
            src_dir = self.get_package_dir(package)

            # Compute package build directory
            build_dir = join(*([self.build_lib] + package.split('.')))

            # Length of path to strip from found files
            if src_dir:
                plen = len(src_dir)+1
            else:
                plen = 0

            # Strip directory from globbed filenames
            filenames = [
                file[plen:] for file in self.find_data_files(package, src_dir)
                ]
            data.append((package, src_dir, build_dir, filenames))
        return data


setup(
    name = "portal1",
    version = "0.1",
    author = u"Luis Belmar-Letelier",
    author_email = "luis@itaapy.com",
    license = "GNU General Public License",
    url = "http://www.ikaaro.org",
    description="Portal 1 (example of itools.cms)",
    package_dir = {'portal1': ''},
    packages = ['portal1'],
    classifiers = ['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Programming Language :: Python',
                   'Topic :: Internet'],
    package_data = {'portal1': ['README', join('ui', 'portal', '*.x*ml')]},
    cmdclass={'build_py': build_py_fixed},
    )
