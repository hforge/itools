#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
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
import sys

# Import from itools
import itools
from itools import vfs
from itools.web import set_context, Context
from itools.cms.server import ask_confirmation
from itools.cms.server import Server


def update(parser, options, target):
    folder = vfs.open(target)

    # Build the server object
    server = Server(target)
    root = server.root

    # Check the version
    instance_version = root.get_property('version')
    class_version = root.class_version
    if instance_version == class_version:
        print 'The instance is up-to-date (version: %s).' % instance_version
        return
    if instance_version > class_version:
        print 'WARNING: the instance (%s) is newer! than the class (%s)' \
              % (instance_version, class_version)
        return

    # Build a fake context
    context = Context(None)
    context.server = server
    set_context(context)

    # Update
    for next_version in root.get_next_versions():
        instance_version = root.get_property('version')
        # Ask
        message = 'Update instance from version %s to version %s (y/N)? ' \
                  % (instance_version, next_version)
        if ask_confirmation(message) is False:
            break
        # Update
        sys.stdout.write('.')
        sys.stdout.flush()
        root.update(next_version)
        sys.stdout.write('.')
        sys.stdout.flush()
        database = server.database
        database.save_changes()
        root.load_state()
        print '.'
    else:
        print '*'
        print '* To finish the upgrade process update the catalog:'
        print '*'
        print '*   $ icms-update-catalog.py %s' % target
        print '*'



if __name__ == '__main__':
    # The command line parser
    usage = '%prog TARGET'
    version = 'itools %s' % itools.__version__
    description = ('Updates the TARGET itools.cms instance (if needed). Use'
                   ' this command when upgrading to a new version of itools.')
    parser = OptionParser(usage, version=version, description=description)

    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    target = args[0]

    # Action!
    update(parser, options, target)
