# -*- coding: UTF-8 -*-
# Copyright (C) 2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


"""
This module provides an upgrade framework.

Whe you upgrade your application to a new version of the software you
may find that the new version requires a different organization of
your data.

This module contains the mixin class Upgrade which will help you to
make the software upgrade process painless.
"""


# Import from Python
import logging


# Initialize logger
logger = logging.getLogger('update')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)


class Upgradeable:
    """
    This class helps to keep in sync an object with its class.

    To do it both the object and the class have a version string, when
    a new instance is created it gets the version string from the class.

    If later you upgrade the software, the method uptodate will tell you
    wether the instance is up to date or not.

    If it isn't the method update must be called to upgrade the instance.
    It is your duty to overwrite this method.
    """

    def __init__(self):
        # Set the object version
        self.__version__ = self.__class__.__version__


    def get_classversion(self):
        """ """
        return self.__class__.__version__


    def get_instanceversion(self):
        """ """
        return self.__version__


    def uptodate(self):
        """
        Returns true if the object is up to date, false otherwise.
        """
        return self.__version__ == self.__class__.__version__


    def update(self, version=None, *args, **kw):
        """
        Updates to the given version.
        """
        # Set zero version if the object does not have a version
        if not self.__dict__.has_key('__version__'):
            self.__version__ = '00000000'

        # Default version to the current class version
        if version is None:
            version = self.__class__.__version__

        # Get all the version numbers
        versions = [ x.split('_')[-1]
                     for x in self.__class__.__dict__.keys()
                     if x.startswith('update_') ]

        # Sort the version numbers
        versions.sort()

        # Filter the versions previous to the current object version
        versions = [ x for x in versions if x > self.__version__ ]

        # Filter the versions next to the given version
        versions = [ x for x in versions if x <= version ]

        # Upgrade
        for version in versions:
            getattr(self, 'update_%s' % version)(*args, **kw)
            logger.info('%s upgraded from %s to %s', self, self.__version__,
                        version)
            self.__version__ = version


