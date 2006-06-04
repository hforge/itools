# -*- coding: ISO-8859-1 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from datetime import tzinfo, timedelta, datetime
from time import strptime

# Import from itools
from itools.handlers.Text import Text
from itools.handlers.registry import register_handler_class
from itools.xml import parser
from itools.datatypes import DataType, Unicode, URI, Integer, String, DateTime


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



# DateTime time zone information
class TZInfo(tzinfo):

    known_time_zones = {
        'GMT': 0, 'UTC': 0, 'UT': 0, # Greenwich Mean Time
        'EDT': -4, 'HAE': -4, # Eastern Daylight Time
        'EST': -5, 'HNE': -5, # Eastern Standard Time
        'CDT': -5, 'HAC': -5, # Central Daylight Time
        'CST': -6, 'HNC': -6, # Central Standard Time
        'MDT': -6, 'HAR': -6, # Mountain Daylight Time
        'MST': -7, 'HNR': -7, # Mountain Standard Time
        'PDT': -7, 'HAP': -7, # Pacific Daylight Time
        'PST': -8, 'HNP': -8  # Pacific Standard Time
    }

    def __init__(self, offset):
        # Offset as sign (+, -) and the number HHMM
        if offset[0] in ('+', '-'):
            # Strip zeros
            off = offset[1:].lstrip('0')
            # Offset in hours with sigh
            off = int(offset[0] + off) / 100
        elif self.known_time_zones.has_key(offset):
            off = self.known_time_zones[offset]
        else:
            off = 0
        self.__offset = timedelta(hours=off)
        self.__name = None


    def utcoffset(self, dt):
        return self.__offset


    def tzname(self, dt):
        return self.__name


    # Implementation without DST
    def dst(self, dt):
        return timedelta(0)



# Encode and decode pubDate and other RSS dates with or without timezone info
class TZDateTime(DataType):

    @staticmethod
    def decode(value):
        # Remove the day name part if exists
        str = value.split(',')[-1].strip()
        # Split date and timezone part if exists
        datetime_parts = str.split(' ')
        date = ' '.join(datetime_parts[0:4])
        if len(datetime_parts) > 4:
            timezone = datetime_parts[4]
        else:
            # UTC is the default timezone
            timezone = 'UTC'
        dt = strptime(date, '%d %b %Y %H:%M:%S')
        tz = TZInfo(timezone)
        return datetime(dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], 0, tz)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        else:
            utc = TZInfo('UTC')
            return value.astimezone(utc).strftime('%Y-%m-%d %H:%M:%S')




# RSS tags types for encode and decode
schema = {'title': Unicode,
          'link': URI,
          'description': Unicode,
          'language': Unicode,
          'copyright': Unicode,
          'pubDate': TZDateTime,
          'ttl': Integer,
          'lastBuildDate': TZDateTime,
          'generatora': Unicode,
          'url': URI,
          'width': Integer,
          'height': Integer,
          'image': String,
          }

# Encode rss element according to its type (by schema)
def decode_element(name, value):
    return schema[name].decode(value)


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


    def new(self):
        self.channel = None


    def _load_state(self, resource):
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
        for event, value, line_number in parser.parse(resource.read()):
            if event == parser.START_ELEMENT:
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
            elif event == parser.END_ELEMENT:
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
            elif event == parser.TEXT and save_data == 1:
                value = decode_element(element_name, value)
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
        self.state.channel = channel
        # Add image element data
        if image:
            self.state.channel.add_image(image)
        # Add channel items
        for i in items:
            self.state.channel.add_item(i)


    def to_str(self, encoding='UTF-8'):
        s = []
        s.append('<?xml version="1.0" encoding="%s"?>' % encoding)
        s.append('<rss version="2.0">')
        s.append('<channel>')
        # Append channel data
        for e in rss_channel_elements:
            if self.state.channel.__dict__.has_key(e):
                # Not None elements (for example channel.image)
                if self.state.channel.__dict__[e]:
                    value = encode_element(e, self.state.channel.__dict__[e])
                    s.append('\t<%s>%s</%s>' % (e, value, e))
        # Append channel image data (if exists)
        image = self.state.channel.get_image()
        if image:
            s.append('\t<image>')
            for e in rss_image_elements:
                if image.__dict__.has_key(e):
                    value = encode_element(e, image.__dict__[e])
                    s.append('\t\t<%s>%s</%s>' % (e, value, e))
            s.append('\t</image>')
        # Append channel items data
        for i in self.state.channel.get_items():
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
        namespace['channel'] = self.state.channel.__dict__
        return namespace


register_handler_class(RSS)
