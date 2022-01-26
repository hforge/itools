# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2007-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@oursours.net>
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
from junitxml import JUnitXmlResult
from sys import exit
from unittest import TestLoader, TestSuite, TextTestRunner

# Import from itools
from itools.core import get_abspath

# Import tests
import test_core
import test_csv
import test_dispatcher
# Test database commentés par l'auteur
# import test_database
import test_datatypes
import test_gettext
import test_handlers
import test_html
import test_i18n
import test_ical
import test_odf
import test_rss
import test_srx
import test_stl
import test_tmx
import test_uri
import test_fs
import test_validators
import test_web
import test_workflow
import test_xliff
import test_xml
import test_xmlfile

test_modules = [test_core, test_csv, test_datatypes, test_dispatcher,
    test_gettext, test_handlers, test_html, test_i18n, test_ical, test_odf,
    test_rss, test_srx, test_stl, test_tmx, test_uri, test_fs,
    test_validators, test_web, test_workflow, test_xliff, test_xml, test_xmlfile]

#test_modules = [test_core, test_csv, test_dispatcher, test_datatypes]

loader = TestLoader()

if __name__ == '__main__':
    usage = '%prog [OPTIONS]'
    description = 'Run ikaaro tests'
    parser = OptionParser(usage, description=description)
    parser.add_option('-m', '--mode', default='standard', help='tests mode')
    options, args = parser.parse_args()
    suite = TestSuite()
    for module in test_modules:
        suite.addTest(loader.loadTestsFromModule(module))
    if options.mode == 'standard':
        ret = TextTestRunner(verbosity=1).run(suite)
    elif options.mode == 'junitxml':
        path = get_abspath('./junit.xml')
        print('Result is here: %s' % path)
        f = file(path, 'wb')
        result = JUnitXmlResult(f)
        result.startTestRun()
        ret = suite.run(result)
        result.stopTestRun()
    exit_code = not ret.wasSuccessful()
    exit(exit_code)
