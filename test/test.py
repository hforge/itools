# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
from unittest import TestCase, TestLoader, TestSuite, TextTestRunner

# Import tests
import test_abnf
import test_csv
import test_datatypes
import test_gettext
import test_handlers
import test_html
import test_http
import test_i18n
import test_ical
import test_odf
import test_pdf
import test_rest
import test_rss
import test_stl
import test_tmx
import test_uri
import test_vfs
import test_web
import test_workflow
import test_xliff
import test_xapian
import test_xml

test_modules = [test_abnf, test_csv, test_datatypes, test_gettext,
    test_handlers, test_html, test_http, test_i18n, test_ical, test_odf,
    test_pdf, test_rest, test_rss, test_stl, test_tmx, test_uri, test_vfs,
    test_web, test_workflow, test_xliff, test_xapian, test_xml]


loader = TestLoader()

if __name__ == '__main__':
    suite = TestSuite()
    for module in test_modules:
        suite.addTest(loader.loadTestsFromModule(module))

    TextTestRunner(verbosity=1).run(suite)
