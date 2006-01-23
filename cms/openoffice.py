# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Nicolas Oyez <noyez@itaapy.com>
#               2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
import mimetypes
import os
import tempfile

# Import from itools
from itools.handlers import get_handler
from itools.stl import stl

# Import from ikaaro
from File import File


mimetypes.add_type('application/vnd.sun.xml.writer', '.sxw')
mimetypes.add_type('application/vnd.sun.xml.calc', '.sxc')
mimetypes.add_type('application/vnd.sun.xml.impress', '.sxi')


class OOffice(File):

    def to_text(self):
        here = os.getcwd()
        path = tempfile.mkdtemp()
        os.chdir(path)
        open('%s/temp.swx' % path, 'w').write(self.to_str())
        os.system('unzip %s/temp.swx' % path)

        try:
            h = get_handler('%s/content.xml' % path)
        except LookupError:
            text = u''
        else:
            text = h.to_text()

        os.system('rm -rf %s' % path)
        os.chdir(here)
        return text


    view__label__ = u'View'
    view__sublabel__ = u'Preview'
    view__access__ = True
    def view(self):
        namespace = {}
        pgraphs = self.to_text()
        pgraphs = [ l for l in pgraphs.split('\n') if l and len(l) > 1 ]
        namespace['pgraphs'] = pgraphs

        handler = self.get_handler('/ui/OOffice_view.xml')
        return stl(handler, namespace)



class OOWriter(OOffice):

    class_id = 'application/vnd.sun.xml.writer'
    class_title = u'Writer'
    class_description = u'Document Writer'
    class_icon48 = 'images/OOWriter48.png'
    class_icon16 = 'images/OOWriter16.png'


File.register_handler_class(OOWriter)



class OOCalc(OOffice):

    class_id = 'application/vnd.sun.xml.calc'
    class_title = u'Calc'
    class_description = u'Document Calc'
    class_icon48 = 'images/OOCalc48.png'
    class_icon16 = 'images/OOCalc16.png'


File.register_handler_class(OOCalc)



class OOImpress(OOffice):

    class_id = 'application/vnd.sun.xml.impress'
    class_title = u'Impress'
    class_description = u'Document Impress'
    class_icon48 = 'images/OOImpress48.png'
    class_icon16 = 'images/OOImpress16.png'

    
File.register_handler_class(OOImpress)
