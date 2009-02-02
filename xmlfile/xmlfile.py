# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007-2008 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2008 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2008 Matthieu France <matthieu@itaapy.com>
# Copyright (C) 2008 Wynand Winterbach <wynand.winterbach@gmail.com>
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
from itools.handlers import TextFile, register_handler_class
from itools.xml import XMLParser, TEXT, stream_to_str
from i18n import get_units, translate



class XMLFile(TextFile):
    """An XML file is represented in memory as a tree where the nodes are
    instances of the classes 'Element' and 'Raw'. The 'Element' class
    represents an XML element, the 'Raw' class represents a text string.

    XML sub-classes will, usually, provide their specific semantics by
    providing their own Element and Raw classes. This is the reason why
    we use 'self.Element' and 'self.Raw' throghout the code instead of
    just 'Element' and 'Raw'.
    """

    class_mimetypes = ['text/xml', 'application/xml']
    class_extension = 'xml'
    __hash__ = None

    def new(self):
        # XML is a meta-language, it does not make change to create a bare
        # XML handler without a resource.
        raise NotImplementedError


    def _load_state_from_file(self, file):
        data = file.read()
        stream = XMLParser(data)
        self.events = list(stream)


    #######################################################################
    # API
    #######################################################################
    def to_str(self, encoding='UTF-8'):
        return stream_to_str(self.events, encoding)


    def set_events(self, events):
        self.set_changed()
        self.events = events


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        return cmp(self.events, other.events)


    def to_text(self):
        """Removes the markup and returns a plain text string.
        """
        text = [ unicode(value, 'utf-8') for event, value, line in self.events
                 if event == TEXT ]
        return u' '.join(text)


    #######################################################################
    # API / Internationalization - Localization
    #######################################################################
    def get_units(self, srx_handler=None):
        return get_units(self.events, srx_handler)


    def translate(self, catalog, srx_handler=None):
        stream = translate(self.events, catalog, srx_handler)
        return stream_to_str(stream)


# Register
register_handler_class(XMLFile)
