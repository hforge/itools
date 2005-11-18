# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Nicolas Oyez <noyez@itaapy.com>
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
import os
import tempfile

# Import from ikaaro
from Handler import Handler
from File import File


class PDF(File):

    class_id = 'application/pdf'
    class_title = u'PDF'
    class_description = u'Document PDF'
    class_icon48 = 'images/Pdf48.png'
    class_icon16 = 'images/Pdf16.png'


    def to_text(self):
        here = os.getcwd()
        pdf_tmp = tempfile.mkdtemp('.pdf')
        os.chdir(pdf_tmp)
        open('./temp.pdf', 'w').write(self.to_str())

        stdin, stdout, stderr = os.popen3('pdftotext ./temp.pdf -')
        text = stdout.read()
        err = stderr.read()
        if err != "":
            print "Warning text of file not indexed because: %s" % err
            text = u''
        else:
            text = unicode(text, 'latin1')

        os.system('rm -fr %s' % pdf_tmp)
        os.chdir(here)

        return text 


    def to_html(self):
        here = os.getcwd()
        pdf_tmp = tempfile.mkdtemp('.pdf')
        os.chdir(pdf_tmp)
        open('./temp.pdf', 'w').write(self.to_str())

        stdin, stdout, stderr = os.popen3(
            'pdftohtml -enc UTF-8 -p -noframes -stdout ./temp.pdf')
        text = stdout.read()
        err = stderr.read()
        if err != "":
            print "ERROR could not generate preview: %s" % err
            text = ''

        os.system('rm -fr %s' % pdf_tmp)
        os.chdir(here)

        return text


    view__access__ = Handler.is_allowed_to_view
    view__label__ = u'View'
    view__sublabel__ = u'Preview'
    def view(self):
        return self.to_html()


File.register_handler_class(PDF)
