# Copyright (C) 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
from itools.html import HTMLParser
from itools.xml import DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, TEXT

if __name__ == '__main__':
    data = open('hello.html').read()
    for type, value, line in HTMLParser(data):
        if type == DOCUMENT_TYPE:
            print 'DOC TYPE  :', repr(value)
        elif type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            print 'START TAG :', tag_name
        elif type == END_ELEMENT:
            tag_uri, tag_name = value
            print 'END TAG   :', tag_name
        elif type == TEXT:
            print 'TEXT      :', value

