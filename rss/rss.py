# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Piotr Macuk <piotr@macuk.pl>
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
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
from datetime import datetime

# Import from itools
from itools.handlers import TextFile, register_handler_class
from itools.xml import XMLParser, XML_DECL, START_ELEMENT, END_ELEMENT
from itools.xml import TEXT, CDATA
from itools.datatypes import Unicode, URI, Integer, String, HTTPDate
from itools.datatypes import XMLContent



# RSS channel elements definition
# See http://www.rssboard.org/rss-specification
rss_channel_elements = {
    'required': ['title', 'link', 'description'],
    'optional': ['language', 'copyright', 'managingEditor', 'webMaster',
        'pubDate', 'lastBuildDate', 'category', 'generator', 'docs', 'cloud',
        'ttl', 'image', 'rating', 'textInput', 'skipHours', 'skipDays']}
rss_image_elements = {
    'required': ['url', 'title', 'link'],
    'optional': ['width', 'height', 'description']}
rss_item_elements = {
    # No specific element but either title or description required
    'required': [],
    'optional': ['title', 'link', 'description', 'author', 'category',
        'comments', 'enclosure', 'guid', 'pubDate', 'source']}


# RSS tags types for encode and decode
schema = {'title': Unicode,
          'link': URI,
          'description': Unicode,
          'copyright': Unicode,
          'pubDate': HTTPDate,
          'ttl': Integer,
          'lastBuildDate': HTTPDate,
          'generator': Unicode,
          'url': URI,
          'width': Integer,
          'height': Integer}


# Encode rss element according to its type (by schema)
def decode_element(name, value, encoding='UTF-8'):
    type = schema.get(name, String)
    if issubclass(type, Unicode):
        return type.decode(value, encoding)
    return type.decode(value)


# Decode rss element according to its type (by schema)
def encode_element(name, value, encoding='UTF-8'):
    # Encode
    type = schema.get(name, String)
    if issubclass(type, Unicode):
        result = type.encode(value, encoding)
    else:
        result = type.encode(value)

    # To XML
    return XMLContent.encode(result)



class RSSFile(TextFile):

    class_mimetypes = ['application/rss+xml']
    class_extension = 'rss'


    def new(self):
        # Channel API
        self.channel = {
            # Required
            'title': None,
            'description': None,
            'link': None,
            # Optional but set sensible default with timezone
            'lastBuildDate': datetime.now()}

        # Image, optional, the API will be a dictionary like the channel
        self.image = None

        # Item API is a list of dictionaries similar to the channel
        self.items = []


    def _load_state_from_file(self, file):
        # Default values
        encoding = 'UTF-8'
        self.channel = {}
        self.image = None
        self.items = []

        data = ''
        stack = []
        for event, value, line_number in XMLParser(file.read()):
            if event == START_ELEMENT:
                namespace_uri, local_name, attributes = value
                if local_name in ('channel', 'image', 'item'):
                    stack.append({})
                else:
                    data = ''
            elif event == END_ELEMENT:
                namespace_uri, local_name = value
                if local_name == 'rss':
                    pass
                elif local_name == 'channel':
                    self.channel = stack.pop()
                elif local_name == 'image':
                    self.image = stack.pop()
                elif local_name == 'item':
                    self.items.append(stack.pop())
                else:
                    value = decode_element(local_name, data, encoding)
                    stack[-1][local_name] = value
                    data = None
            elif event == TEXT or event == CDATA:
                if data is not None:
                    data += value
            elif event == XML_DECL:
                # Will overwrite the 'encoding' defaut value
                # Others are ignored
                version, encoding, standalone = value


    def to_str(self, encoding='UTF-8'):
        s = []

        s.append('<?xml version="1.0" encoding="%s"?>' % encoding)
        s.append('<rss version="2.0">')
        s.append('  <channel>')

        # Append channel
        channel = self.channel
        # Required
        for name in rss_channel_elements['required']:
            value = channel[name]
            data = encode_element(name, value, encoding)
            s.append('    <%s>%s</%s>' % (name, data, name))
        # Optional
        for name in rss_channel_elements['optional']:
            value = channel.get(name)
            if value is None:
                continue
            data = encode_element(name, value, encoding)
            s.append('    <%s>%s</%s>' % (name, data, name))

        # Append image
        image = self.image
        if image:
            s.append('    <image>')
            # Required
            for name in rss_image_elements['required']:
                value = image[name]
                data = encode_element(name, value, encoding)
                s.append('      <%s>%s</%s>' % (name, data, name))
            # Optional
            for name in rss_image_elements['optional']:
                value = image.get(name)
                if value is None:
                    continue
                data = encode_element(name, value, encoding)
                s.append('      <%s>%s</%s>' % (name, data, name))
            s.append('    </image>')

        # Append items
        for item in self.items:
            s.append('    <item>')
            # Required
            for name in rss_item_elements['required']:
                value = item[name]
                if value is None:
                    continue
                data = encode_element(name, value, encoding)
                s.append('      <%s>%s</%s>' % (name, data, name))
            # Optional
            for name in rss_item_elements['optional']:
                value = item.get(name)
                if value is None:
                    continue
                data = encode_element(name, value, encoding)
                s.append('      <%s>%s</%s>' % (name, data, name))
            s.append('    </item>')

        s.append('  </channel>')
        s.append('</rss>')
        return '\n'.join(s)



register_handler_class(RSSFile)
