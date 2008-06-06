# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from pdf import PDFFile
from itools.utils import get_abspath
from itools.xml import register_dtd

# Import from reportlab
try:
    from rml import rmltopdf, stl_rmltopdf
    from rml2 import rml2topdf, rml2topdf_test, normalize
except ImportError:
    print 'You need to install the package "reportlab" to get RML working.'
    def rmltopdf(*args, **kw):
        raise NotImplementedError, 'the package "reportlab" must be installed'
    stl_rmltopdf = rmltopdf


__all__ = ['PDFFile', 'rmltopdf', 'stl_rmltopdf',
           'rml2topdf', 'rml2topdf_test', 'normalize']


# Register "rml.dtd"
register_dtd(get_abspath('rml.dtd'), uri='rml_1_0.dtd')
register_dtd(get_abspath('rml.dtd'), uri='rml.dtd')

