#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@itaapy.com>
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from sys import path
from optparse import OptionParser
from os import sep

# Import from itools
from itools import utils, __version__
from itools.utils import list_eggs_info


if __name__ == '__main__':
    # command line parsing
    usage = '%prog [OPTIONS]'
    version = 'itools %s' % __version__
    description = ("List available python packages from site-packages")
    parser = OptionParser(usage, version=version, description=description)
    parser.parse_args()


    # find the site-packages absolute path
    sites = set([])
    for dir in path:
        if 'site-packages' in dir:
            dir = dir.split(sep)
            sites.add(sep.join(dir[:dir.index('site-packages')+1]))

    # List available modules
    for site in sites:
        print "Packages for %s :" % site
        list_eggs_info(site)
        print
