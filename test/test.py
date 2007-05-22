# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import os
from unittest import TestCase, TestLoader, TestSuite, TextTestRunner

# Import tests
import test_catalog
import test_cms
import test_csv
import test_datatypes
import test_gettext
import test_handlers
import test_html
import test_http
import test_i18n
import test_ical
import test_pdf
import test_rss
import test_schemas
import test_stl
import test_tmx
import test_uri
import test_vfs
import test_web
import test_workflow
import test_xhtml
import test_xliff
import test_xml


test_modules = [test_catalog, test_cms, test_csv, test_datatypes,
    test_gettext, test_handlers, test_html, test_http, test_i18n, test_ical,
#    test_pdf, test_rest,
    test_rss, test_schemas, test_stl, test_tmx, test_uri, test_vfs,
    test_web, test_workflow, test_xhtml, test_xliff, test_xml]


loader = TestLoader()

if __name__ == '__main__':
    suite = TestSuite()
    for module in test_modules:
        suite.addTest(loader.loadTestsFromModule(module))

    TextTestRunner(verbosity=1).run(suite)
