# Copyright (C) 2010 J. David Ibáñez <jdavid.ibp@gmail.com>

from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, TEXT

data ="""
<x xmlns="namespace1" xmlns:n2="namespace2" >
  <test a="1" n2:b="2" />
</x>
"""


if __name__ == '__main__':
    for type, value, line in XMLParser(data):
        if type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            print 'START TAG :', tag_name, attributes
        elif type == END_ELEMENT:
            tag_uri, tag_name = value
            print 'END TAG   :', tag_name
        elif type == TEXT:
            print 'TEXT      :', value

