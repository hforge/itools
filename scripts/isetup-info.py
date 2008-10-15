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
from optparse import OptionParser

# Import from itools
from itools import __version__
from itools.isetup import packages_infos


if __name__ == '__main__':
    # command line parsing
    usage = '%prog [package name]'
    version = 'itools %s' % __version__
    description = ("Print available informations for a python package")
    parser = OptionParser(usage, version=version, description=description)

    parser.add_option("-l", "--list",
                      dest="list", default=False, action="store_true",
                      help="List available python packages from site-packages")

    (options, args) = parser.parse_args()

    if len(args) != 1 and not options.list:
        parser.error('Please enter a package name')

    module_name = args[0] if not options.list else None

    found = False

    for site, packages in packages_infos(module_name):
        if options.list:
            print "packages in %s" % site
        else:
            print "package found in %s" % site
        for name, data, origin in packages:
            found = True
            print "%s %-20.20s %-25.25s" % (origin, name, data['version'])

        if options.list:
            print
            continue

        for key in data:
            if type(data[key]) in [type([]), type(())]:
                for val in data[key]:
                    print "  %s %s" % (key + ':', val)
            else:
                print "  %s %s" % (key + ':', data[key])
        print

    if found:
        print "The first letter tells from where data is read:"
        print "  E: .egg-info, M: standard package, S: itools package"
    else:
        print "No matching package found"

