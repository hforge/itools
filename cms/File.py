# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
import itools
from itools.uri import get_reference
from itools.stl import stl
from itools.web.exceptions import UserError
from itools.web import get_context

# Import from ikaaro
from utils import comeback
from Handler import Handler


class File(Handler, itools.handlers.File.File):

    class_id = 'file'
    class_title = u'File'
    class_description = u'Upload office documents, images, media files, etc.'
    class_version = '20040625'
    class_icon16 = 'images/File16.png'
    class_icon48 = 'images/File48.png'


    @classmethod
    def new_instance_form(cls):
        handler = get_context().root.get_handler('ui/File_new_instance.xml')
        return stl(handler)


    GET__mtime__ = Handler.get_mtime
    def GET(self):
        return self.download()


    #######################################################################
    # API
    #######################################################################
    def get_size(self):
        """
        Returns the size of this object.
        """
        return self.resource.get_size()


    #######################################################################
    # User interface
    #######################################################################
    def get_views(self):
        return ['download_form', 'externaledit', 'edit_metadata_form']


    def get_subviews(self, name):
        if name in ['externaledit', 'upload_form']:
            return ['externaledit', 'upload_form']
        if name in ['download_form', 'view']:
            if hasattr(self, 'view'):
                return ['download_form', 'view']
            else:
                return ['download_form']
        return []


    #######################################################################
    # Download
    download_form__access__ = Handler.is_allowed_to_view
    download_form__label__ = u'View'
    download_form__sublabel__ = u'Download'
    def download_form(self):
        namespace = {}
        namespace['url'] = '../' + self.name
        namespace['title_or_name'] = self.get_title_or_name()
        handler = self.get_handler('/ui/File_download_form.xml')
        return stl(handler, namespace)


    download__access__ = Handler.is_allowed_to_view
    download__mtime__ = Handler.get_mtime
    def download(self):
        context = get_context()
        request, response = context.request, context.response

        # Content-Type
        metadata = self.get_metadata()
        if metadata is None:
            mimetype = self.get_mimetype()
        else:
            mimetype = self.get_property('format')
        response.set_header('Content-Type', mimetype)

        return self.to_str()


    #######################################################################
    # Edit / External
    externaledit__access__ = Handler.is_allowed_to_edit
    externaledit__label__ = u'Edit'
    externaledit__sublabel__ = u'External'
    def externaledit(self):
        handler = self.get_handler('/ui/File_externaledit.xml')
        return stl(handler)


    external_edit__access__ = Handler.is_allowed_to_edit
    def external_edit(self, encoding=None, **kw):
        # TODO check if zopeedit really needs the meta_type.

        # Get the context, request and response
        context = get_context()
        request, response = context.request, context.response
        # Get the resource
        resource = self.resource
        object = resource._get_object()

        uri = context.uri
        uri_string = '%s://%s/%s' % (uri.scheme, uri.authority, uri.path[:-1])
        uri = get_reference(uri_string)
        r = ['url:%s' % str(uri),
             'meta_type:toto', ##% object.meta_type,
             'content_type:%s' % resource.get_mimetype(),
             'cookie:%s' % request.get_cookies_as_str()]

        title = self.get_property('dc:title')
        if title:
            title = title.encode(encoding or 'UTF-8')
        else:
            title = self.name
        r.append('title:%s' % title)

        if resource.is_locked():
            # Object is locked, send down the lock token 
            # owned by this user (if any)
            user = context.user
            for lock in object.wl_lockValues():
                if not lock.isValid():
                    continue # Skip invalid/expired locks
                creator = lock.getCreator()
                if creator and creator[1] == user.name:
                    # Found a lock for this user, so send it
                    r.append('lock-token:%s' % lock.getLockToken())
                    if request.get('borrow_lock'):
                        r.append('borrow_lock:1')
                    break

        r.append('')

        # TODO known bug from ExternalEditor requires rfc1123_date()
        # Using RESPONSE.setHeader('Pragma', 'no-cache') would be better, but
        # this chokes crappy most MSIE versions when downloads happen on SSL.
        # cf. http://support.microsoft.com/support/kb/articles/q316/4/31.asp
        #response.set_header('Last-Modified', rfc1123_date())
        response.set_header('Pragma', 'no-cache')

        # Encoding
        if encoding is None:
            r.append(self.to_str())
        else:
            r.append(self.to_str(encoding))

        data = '\n'.join(r)

        response.set_header('Content-Type', 'application/x-zope-edit')
        return data


    #######################################################################
    # Edit / Upload
    upload_form__access__ = Handler.is_allowed_to_edit
    upload_form__label__ = u'Edit'
    upload_form__sublabel__ = u'Upload'
    def upload_form(self):
        handler = self.get_handler('/ui/File_upload.xml')
        return stl(handler)


    upload__access__ = Handler.is_allowed_to_edit
    def upload(self, file=None, **kw):
        if file is None:
            raise UserError, self.gettext(u'No file has been entered.')

        # Check wether the handler is able to deal with the uploaded file
        try:
            self.load_state(file)
        except:
            self.load_state()
            raise UserError, self.gettext(u'Upload failed: either the file does not match this document type (%s) or it contains errors.') % self.get_mimetype()

        message = self.gettext(u'Version uploaded.')
        comeback(message)


Handler.register_handler_class(File)
