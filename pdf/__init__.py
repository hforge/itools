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
from itools.relaxng import RelaxNGFile
from itools.xml import register_dtd, register_namespace

# There are imports from ReportLab in these imports, so, ...
try:
    from rml import rmltopdf, stl_rmltopdf
    from rml2 import rml2topdf, stl_rml2topdf
except ImportError:
    print 'You need to install the package "reportlab" to get RML working.'

    # Not implemented, ...
    def not_implemented(*args, **kw):
        raise NotImplementedError, 'the package "reportlab" must be installed'
    rmltopdf = not_implemented
    stl_rmltopdf = not_implemented
    rml2topdf = not_implemented
    stl_rml2topdf = not_implemented


__all__ = ['PDFFile', 'rmltopdf', 'stl_rmltopdf',
           'rml2topdf', 'rml2topdf_test', 'normalize', 'paragraph_stream',
           'param']

# Register "rml.dtd"
register_dtd(get_abspath('rml.dtd'), uri='rml_1_0.dtd')
register_dtd(get_abspath('rml.dtd'), uri='rml.dtd')

# Read the Relax NG schema of PML and register its namespace
rng_file = RelaxNGFile(get_abspath('PML-schema.rng'))
rng_file.auto_register()

