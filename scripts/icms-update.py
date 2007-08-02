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
from ConfigParser import RawConfigParser
from optparse import OptionParser
import sys

# Import from itools
import itools
from itools.uri import get_reference, get_absolute_reference2
from itools import vfs
from itools.catalog import make_catalog, Catalog
from itools.handlers import Config
from itools.web import set_context, Context
from itools.cms.database import DatabaseFS
from itools.cms.server import ask_confirmation
from itools.cms.server import Server, get_root_class, get_config


def update(parser, options, target):
    folder = vfs.open(target)

    # Update the config file (renamed from "config.ini" to "config.conf")
    # XXX Remove for 0.17
    if folder.exists('config.ini'):
        message = ('Update config file (will rename "config.ini" to'
                   ' "config.conf")? (y/N)')
        if ask_confirmation(message) is False:
            return
        print '  * Updating the configuration file...'
        # Load the old config file
        old_config = RawConfigParser()
        #old_config.add_section('instance')
        old_config.read(['%s/config.ini' % target])
        # Read the different options
        kw = {}
        for name in old_config.options('instance'):
            kw[name] = old_config.get('instance', name)
        # Remove the obsolete option "root"
        if 'root' in kw:
            if 'modules' in kw:
                del kw['root']
            else:
                kw['modules'] = kw['root']
        # Create the new config file
        new_config = Config(**kw)
        new_config.save_state_to('%s/config.conf' % target)
        # Remove the old confi file
        folder.remove('config.ini')

    # Update the database, add "database/.catalog.bak" and remove
    # "database.bak"
    # XXX Remove for 0.17
    if folder.exists('database.bak'):
        message = ('Update database (will remove "database.bak" and add '
                   '"database/.catalog.bak")? (y/N)')
        if ask_confirmation(message) is False:
            return
        print '  * Removing "database.bak"...'
        folder.remove('database.bak')
        print '  * Adding "database/.catalog.bak"...'
        folder.copy('database/.catalog', 'database/.catalog.bak')

    # Update the catalog
    # XXX Remove for 0.17
    if folder.exists('database/.catalog'):
        message = ('Update database (will move the catalog out of the '
                   'database folder)? (y/N)')
        if ask_confirmation(message) is False:
            return
        print '  * Remove "database/.catalog" ...'
        folder.remove('database/.catalog')
        folder.remove('database/.catalog.bak')
        print '  * Create "catalog" ...'
        # Load Python packages and modules
        aux = get_absolute_reference2(target)
        config = get_config(aux)
        modules = config.get_value('modules')
        if modules is not None:
            for name in modules.split():
                name = name.strip()
                exec('import %s' % name)

        cls = get_root_class(aux.resolve2('database'))
        catalog = make_catalog('%s/catalog' % target, *cls._catalog_fields)

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
        database.commit()
        root.load_state()
        print '.'
    else:
        print '*'
        print '* To finish the upgrade process update the catalog:'
        print '*'
        print '*   $ icms-update-catalog %s' % target
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
