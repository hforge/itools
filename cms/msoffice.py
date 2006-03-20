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

# Import from itools
from itools.handlers.Text import Text

# Import from ikaaro
from Handler import Handler
from File import File



class MSOffice(File):

    def to_text(self):
        here = os.getcwd()
        doc_tmp = tempfile.mkdtemp('.doc')
        os.chdir(doc_tmp)
        open('./temp.doc', 'w').write(self.to_str())

        cmd = self.cmd_to_convert 
        stdin, stdout, stderr = os.popen3(cmd)
        stderr = stderr.read()
        if stderr != "":
            print "Warning text of file not indexed: %s" % stderr
            text = u''
        else:
            text = unicode(stdout.read(), 'latin1')

        os.system('rm -fr %s' % doc_tmp)
        os.chdir(here)

        return text 


    ########################################################################
    # User interface
    ########################################################################
    view__access__ = Handler.is_allowed_to_view
    view__label__ = u'View'
    view__sublabel__ = u'Preview'
    def view(self):
        return self.to_html()



class MSWord(MSOffice):

    class_id = 'application/msword'
    class_title = u'Word'
    class_description = u'Document Word'
    class_icon48 = 'images/Word48.png'
    class_icon16 = 'images/Word16.png'


    def to_text(self):
        stdin, stdout, stderr = os.popen3('catdoc')
        stdin.write(self.to_str())
        stdin.close()
        return unicode(stdout.read(), 'latin1')


    def to_html(self):
        here = os.getcwd()
        doc_tmp = tempfile.mkdtemp('.doc')
        os.chdir(doc_tmp)
        open('./temp.doc', 'w').write(self.to_str())

        # error and result are both directed to stdout by wvHtml
        cmd = 'wvHtml ./temp.doc -'
        stdin, stdout, stderr = os.popen3(cmd)
        text = stdout.read()
        encoding = Text.guess_encoding(text)
        text = unicode(text, encoding)
        os.system('rm -fr %s' % doc_tmp)
        os.chdir(here)    

        return text
        

        

File.register_handler_class(MSWord)



class MSExcel(MSOffice):

    class_id = 'application/vnd.ms-excel'
    class_title = u'Excel'
    class_description = u'Document Excel'
    class_icon48 = 'images/Excel48.png'
    class_icon16 = 'images/Excel16.png'
    class_extension = '.xls'
    cmd_to_convert = 'xlhtml ./temp.doc | links -dump'


    def to_html(self):
        here = os.getcwd()
        doc_tmp = tempfile.mkdtemp('.doc')
        os.chdir(doc_tmp)
        open('./temp.doc', 'w').write(self.to_str())

        stdin, stdout, stderr = os.popen3('xlhtml ./temp.doc')
        err = stderr.read()
        if err != "":
            print "Error could not generate preview because: %s" % err
            text = u''
        else:
            text = unicode(stdout.read(), 'latin1')

        os.system('rm -fr %s' % doc_tmp)
        os.chdir(here)    

        return text


File.register_handler_class(MSExcel)



class MSPowerPoint(MSOffice):

    class_id = 'application/vnd.ms-powerpoint'
    class_title = u'PowerPoint'
    class_description = u'Document PowerPoint'
    class_icon48 = 'images/PowerPoint48.png'
    class_icon16 = 'images/PowerPoint16.png'
    class_extension = '.ppt'
    cmd_to_convert = ('ppthtml ./temp.doc | '
                      'iconv -f utf8 -t latin1 | links -dump')


    def to_html(self):
        here = os.getcwd()
        doc_tmp = tempfile.mkdtemp('.doc')
        os.chdir(doc_tmp)
        open('./temp.doc', 'w').write(self.to_str())

        stdin, stdout, stderr = os.popen3('ppthtml ./temp.doc')
        err = stderr.read()
        if err != "":
            print "Error could not generate preview because: %s" % err
            text = u''
        else:
            text = unicode(stdout.read(), 'utf8')

        os.system('rm -fr %s' % doc_tmp)
        os.chdir(here)

        return text


File.register_handler_class(MSPowerPoint)
