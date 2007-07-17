# -*- coding: UTF-8 -*-
# Copyright (C) ${YEAR} ${AUTHOR_NAME} <${AUTHOR_EMAIL}>
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
from itools import get_abspath
from itools.uri import Path
from itools.web import get_context
from itools.stl import stl

# Import from itools.cms
from itools.cms.skins import Skin, register_skin


class FrontOffice1(Skin):

    def template(self, content):
        """Skin template."""
        context = get_context()
        here, root = context.handler, context.root

        # Namespace
        namespace = {}

        # The breadcrumb
        new_bc = []
        for dic in Skin.get_breadcrumb(self, context):
            dic['url'] = dic['url'].split(';')[0] + ';view'
            new_bc.append(dic)    
        namespace['breadcrumb'] = new_bc
        
        # The first folder
        current_path = here.get_abspath()
        folders = [{
            'url': '%s/;view' % here.get_pathto(handler), 
            'name': handler.get_title(),
            'in_path': current_path.startswith(handler.get_abspath())}
                for handler in root.search_handlers(format='ExampleFolder')]
        namespace['folders'] = folders    
        
        ac = here.get_access_control()
        is_allowed_to_edit = ac.is_allowed_to_edit(context.user, here)
        namespace['is_allowed_to_edit'] = is_allowed_to_edit

        namespace['switch_skin'] = ";switch_skin"

        # content, here our template have only one "slot": content
        namespace['body'] = content

        # Set the encoding to UTF-8
        context.response.set_header('Content-Type', 'text/html; charset=UTF-8')

        # Load the template
        handler = self.get_handler('/ui/frontoffice1/template.xhtml')

        # Build the header
        header = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"\n'\
                 '  "http://www.w3.org/TR/html4/strict.dtd">\n'
        # Build the body
        prefix = Path(handler.get_abspath())
        body = stl(handler, namespace, prefix=prefix)

        return header + body

