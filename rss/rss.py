# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Piotr Macuk <piotr@macuk.pl>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from itools.handlers import Text, register_handler_class
from itools.xml import Parser, XML_DECL, START_ELEMENT, END_ELEMENT, TEXT
from itools.datatypes import (is_datatype, Unicode, URI, Integer, String,
    InternetDateTime)


# Rss channel elements definition
rss_elements = {
    'channel': {
        'required': ['title', 'link', 'description'],
        'optional': ['language', 'copyright', 'pubDate', 
                     'ttl', 'image', 'lastBuildDate', 'generator']
    },
    'image': {
        'required': ['url', 'title', 'link'],
        'optional': ['width', 'height', 'description']
    },
    'item': {
        'required': [],
        'optional': ['title', 'link', 'description', 'pubDate']
    }
}
rss_channel_elements = rss_elements['channel']['required'] + \
                       rss_elements['channel']['optional']
rss_image_elements = rss_elements['image']['required'] + \
                     rss_elements['image']['optional']
rss_item_elements = rss_elements['item']['required'] + \
                    rss_elements['item']['optional']
rss_all_elements = rss_channel_elements + rss_image_elements + \
                   rss_item_elements



# RSS tags types for encode and decode
schema = {'title': Unicode,
          'link': URI,
          'description': Unicode,
          'language': Unicode,
          'copyright': Unicode,
          'pubDate': InternetDateTime,
          'ttl': Integer,
          'lastBuildDate': InternetDateTime,
          'generatora': Unicode,
          'url': URI,
          'width': Integer,
          'height': Integer,
          'image': String,
          }

# Encode rss element according to its type (by schema)
def decode_element(name, value, encoding='utf-8'):
    type = schema[name]
    if is_datatype(type, Unicode):
        return type.decode(value, encoding)
    return type.decode(value)


# Decode rss element according to its type (by schema)
def encode_element(name, value):
    return schema[name].encode(value)



class RssChannel(object):

    def __init__(self, title, link, description):
        self.title = title
        self.link = link
        self.description = description
        self.items = []
        self.image = None


    # Add item to the channel
    def add_item(self, item):
        self.items.append(item)


    # Get channel items
    def get_items(self):
        return self.items


    # Add image data to the channel
    def add_image(self, image):
        self.image = image


    # Get channel image data
    def get_image(self):
        return self.image


    # Add additional elements
    def add_elements(self, elements):
        for k in elements.keys():
            if not self.__dict__.has_key(k) and k in rss_channel_elements:
                self.__dict__[k] = elements[k]



class RssChannelItem(object):

    def __init__(self, title, link, description):
        self.title = title
        self.link = link
        self.description = description


    # Add additional elements
    def add_elements(self, elements):
        for k in elements.keys():
            if not self.__dict__.has_key(k) and k in rss_item_elements:
                self.__dict__[k] = elements[k]



class RssChannelImage(object):

    def __init__(self, url, title, link):
        self.url = url
        self.title = title
        self.link = link


    # Add additional elements
    def add_elements(self, elements):
        for k in elements.keys():
            if not self.__dict__.has_key(k) and k in rss_image_elements:
                self.__dict__[k] = elements[k]



class RSS(Text):

    class_mimetypes = ['application/rss+xml']
    class_extension = 'rss'

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'channel']


    def new(self):
        self.channel = None


    def _load_state_from_file(self, file):
        encoding = 'utf-8'
        # Temp fields data
        fields = {}
        channel_fields = {}
        # Save text data indicator
        save_data = 0
        # Inside tag indicators
        inside_image = 0
        inside_item = 0
        # Name of the saved element
        element_name = ''
        # Temp objects
        channel = None
        image = None
        items = []
        # Parse the rss file
        for event, value, line_number in Parser(file.read()):
            if event == XML_DECL:
                version, encoding, standalone = value
            elif event == START_ELEMENT:
                namespace, local_name, attributes = value
                if local_name == 'image':
                    inside_image = 1
                elif local_name == 'item':
                    inside_item = 1
                if local_name in rss_all_elements:
                    save_data = 1
                    element_name = local_name
                else:
                    save_data = 0
            elif event == END_ELEMENT:
                namespace, local_name = value
                # Save item data
                if local_name == 'item':
                    item = RssChannelItem(fields['title'], 
                                          fields['link'],
                                          fields['description'])
                    # Add other (optional) elements
                    item.add_elements(fields)
                    items.append(item)
                    inside_item = 0
                    fields = {}
                # Save image data
                elif local_name == 'image':
                    image = RssChannelImage(fields['url'], 
                                            fields['title'],
                                            fields['link'])
                    # Add other (optional) elements
                    image.add_elements(fields)
                    inside_image = 0
                    fields = {}
            elif event == TEXT and save_data == 1:
                value = decode_element(element_name, value, encoding)
                if inside_image == 1 or inside_item == 1:
                    fields[element_name] = value
                else:
                    channel_fields[element_name] = value
                save_data = 0

        # Fill the internal data structure
        channel = RssChannel(channel_fields['title'],
                             channel_fields['link'],
                             channel_fields['description'])
        # Add other (optional) elements
        channel.add_elements(channel_fields)
        self.channel = channel
        # Add image element data
        if image:
            self.channel.add_image(image)
        # Add channel items
        for i in items:
            self.channel.add_item(i)


    def to_str(self, encoding='UTF-8'):
        s = []
        s.append('<?xml version="1.0" encoding="%s"?>' % encoding)
        s.append('<rss version="2.0">')
        s.append('<channel>')
        # Append channel data
        for e in rss_channel_elements:
            if self.channel.__dict__.has_key(e):
                # Not None elements (for example channel.image)
                if self.channel.__dict__[e]:
                    value = encode_element(e, self.channel.__dict__[e])
                    s.append('\t<%s>%s</%s>' % (e, value, e))
        # Append channel image data (if exists)
        image = self.channel.get_image()
        if image:
            s.append('\t<image>')
            for e in rss_image_elements:
                if image.__dict__.has_key(e):
                    value = encode_element(e, image.__dict__[e])
                    s.append('\t\t<%s>%s</%s>' % (e, value, e))
            s.append('\t</image>')
        # Append channel items data
        for i in self.channel.get_items():
            s.append('\t<item>')
            for e in rss_item_elements:
                if i.__dict__.has_key(e):
                    value = encode_element(e, i.__dict__[e])
                    s.append('\t\t<%s>%s</%s>' % (e, value, e))
            s.append('\t</item>')
        s.append('</channel>')
        s.append('</rss>')
        return '\n'.join(s)


    # Return namespace to use with STL template
    def get_namespace(self):
        namespace = {}
        namespace['channel'] = self.channel.__dict__
        return namespace


register_handler_class(RSS)
