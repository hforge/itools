#!/usr/bin/env python


# Import from itools
from itools import get_abspath
from itools.handlers import get_handler


if __name__ == '__main__':
    # Output the HTTP headers
    print "Content-Type: text/html"
    print

    # Load the STL template
    path = get_abspath(globals(), 'hello.xml')
    handler = get_handler(path)

    # Build the namespace
    namespace = {'title': 'hello world!!'}

    # Process and output the template
    print handler.stl(namespace)
