# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.handlers.Folder import Folder

# Import from itools.lucene
import Lucene
import Segment


class Segments(Lucene.File):

    def _load(self):
        """
        Load the segments into memory as a dictionary <name>: <size>
        """
        self.data = self.resource.get_data()
        self.index = 0
        # Parse
        count = self.load_uint32()
        self.segments = {}
        for i in range(count):
            name = self.load_string()
            size = self.load_uint32()
            self.segments[name] = size

        if self.index < len(self.data):
            raise ValueError, 'the file size is bigger than expected'
        # Remove temporal data
        del self.data
        del self.index


    def get_skeleton(self, segments=[]):
        data = self.save_uint32(len(segments))
        for segment_name in segments:
            data += self.save_string(segment_name)
            data += self.save_uint32(0)
        return data


    def __str__(self):
        data = self.save_uint32(len(self.segments))
        for name, size in self.segments.items():
            data += self.save_string(name)
            data += self.save_uint32(size)
        return data



class Deletable(Lucene.File):
    def _load(self):
        self.data = self.resource.get_data()
        self.index = 0
        # Parse
        n = self.load_unit32()
        self.deleted_files = []
        for i in range(n):
            name = self.load_string()
            self.deleted_files.append(name)

        if self.index < len(self.data):
            raise ValueError, 'the file size is bigger than expected'
        # Remove temporal data
        del self.data
        del self.index


    def get_skeleton(self):
        return self.save_uint32(0)



class Index(Folder):
    def _get_handler(self, segment):
        name = segment.name
        if self.has_resource(name):
            resource = self.get_resource(name)
            if name == 'segments':
                return Segments(resource)
            elif name == 'deletable':
                return Deletable(resource)
            elif name.count('.') == 1:
                # Maybe it is a segment file
                segments = self.get_handler('segments')
                name, extension = name.split('.')
                if name in segments.segments:
                    # It really looks like a segment file
                    if extension == 'fnm':
                        return Lucene.FieldInfos(resource)
                    elif extension == 'fdx':
                        ndocs = segments.segments[name]
                        return Lucene.FieldIndex(resource, num_docs=ndocs)
                    elif extension == 'fdt':
                        ndocs = segments.segments[name]
                        return Lucene.FieldData(resource, num_docs=ndocs)
                    elif extension == 'tis':
                        return Lucene.TermInfoFile(resource)
                    elif extension == 'tii':
                        return Lucene.TermInfoIndex(resource)
                    elif extension == 'frq':
                        tis = self.get_handler('%s.tis' % name)
                        num_terms = tis.term_count
                        return Lucene.FreqFile(resource, num_terms=num_terms)
                    elif extension == 'prx':
                        tis = self.get_handler('%s.tis' % name)
                        num_terms = tis.term_count
                        return Lucene.ProxFile(resource, num_terms=num_terms)
                    elif extension == 'tvx':
                        ndocs = segments.segments[name]
                        return Lucene.DocumentIndex(resource, num_docs=ndocs)
                    elif extension == 'tvd':
                        ndocs = segments.segments[name]
                        return Lucene.Document(resource, num_docs=ndocs)
                    elif extension == 'tvf':
                        tvd = self.get_handler('%s.tvd' % name)
                        nfields = tvd.get_nfields()
                        return Lucene.Field(resource, num_fields=nfields)
                    elif extension == 'del':
                        return Lucene.DeletedDocuments(resource)
                    elif extension[0] == 'f':
                        # XXX Normalization
                        pass
        return Folder._get_handler(self, segment)


    def get_skeleton(self, fields=[]):
        """
        The parameter 'fields' must be a list
        """
        skeleton = []
        skeleton.append(('segments', Segments(segments=['000'])))
        skeleton.append(('000.fnm', Lucene.FieldInfos(fields=fields)))
        skeleton.append(('000.fdx', Lucene.FieldIndex()))
        skeleton.append(('000.fdt', Lucene.FieldData()))
        skeleton.append(('000.tis', Lucene.TermInfoFile()))
        skeleton.append(('000.tii', Lucene.TermInfoIndex()))
        skeleton.append(('000.frq', Lucene.FreqFile()))
        skeleton.append(('000.prx', Lucene.ProxFile()))
        skeleton.append(('000.tvx', Lucene.DocumentIndex()))
        skeleton.append(('000.tvd', Lucene.Document()))
        skeleton.append(('000.tvf', Lucene.Field()))
        return skeleton


    def _load(self):
        segments = self.get_handler('segments')

        self.segments = {}
        for segment_name in segments.segments.keys():
            self.segments[segment_name] = Segment.Segment(self, segment_name)


    #########################################################################
    # API
    #########################################################################
    def index_document(self, document):
        segments_handler = self.get_handler('segments')
        # Get the segment name
        segment_names = segments_handler.segments.keys()
        segment_names.sort()
        segment_name = segment_names[-1]
        # Incremet the segment size
        segments_handler.segments[segment_name] += 1
        # Get the segment
        segment = self.segments[segment_name]
        # Index the document
        doc_number = segment.index_document(document)
        # Save the data
        segments_handler.save()
        # Return the document number
        return doc_number


    def unindex_document(self, doc_number):
        segments_handler = self.get_handler('segments')
        # Get the segment name
        segment_names = segments_handler.segments.keys()
        segment_names.sort()
        segment_name = segment_names[-1]
        # Decremet the segment size
        segments_handler.segments[segment_name] -= 1
        # Get the segment
        segment = self.segments[segment_name]
        # Unindex the document
        segment.unindex_document(doc_number)
        # Save the data
        segments_handler.save()
        segment.save()



    def search(self, **kw):
        # Get the segment name
        for segment_name, segment in self.segments.items():
            return segment.search(**kw)
