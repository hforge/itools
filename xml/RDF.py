# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ib��ez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


# Import from itools
import XML


##class Subject(object):
##    def __init__(self):



class RDF(XML.Document):
    def _load(self):
        XML.Document._load(self)

        self.graph = {}
        for node in self.traverse():
            if isinstance(node, XML.Element):
                if isinstance(node, Description):
                    subject = node.attributes['about'].value
                    self.graph.setdefault(subject, [])
                else:
                    parent = node.parent
                    if isinstance(parent, Description):
                        subject = parent.attributes['about'].value
                        predicate = node.name
                        object = unicode(node.children)
                        self.graph[subject].append((predicate, object))



########################################################################
# Elements
class Description(XML.Element):
    pass
##    namespace = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'


########################################################################
# Register
class NSHandler(object):
    def get_element(self, prefix, name):
        if name == 'Description':
            return Description(prefix, name)
        return XML.Element(prefix, name)


    def get_attribute(self, prefix, name, value):
        return XML.Attribute(prefix, name, value)



XML.registry.set_namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                           NSHandler())
XML.registry.set_namespace('http://purl.org/dc/elements/1.1/', NSHandler())
