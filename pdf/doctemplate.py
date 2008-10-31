# -*- coding: UTF-8 -*-

# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Fabrice Decroix <fabrice.decroix@gmail.com>
# Copyright (C) 2008 Yannick Martel <yannick.martel@gmail.com>
# Copyright (C) 2008 Dumont Sébastien <sebastien.dumont@itaapy.com>
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


from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame

import copy



class MySimpleDocTemplate(BaseDocTemplate):
    """
        The document template used for all PDF documents.
    """


    def __init__(self, filename, context, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)
        self.toc_index = 0
        body_attrs = (self.leftMargin, self.bottomMargin, self.width,
                      self.height)
        self.main_frame_attr = {'x1': self.leftMargin,
                                'y1': self.bottomMargin,
                                'width': self.width,
                                'height': self.height,
                                'id':'normal',
                                'showBoundary': self.showBoundary}

        # We keep the main frame reference to resize it during the build
        self.main_frame = Frame(**self.main_frame_attr)
        self.main_frame_change = False
        template_attrs = {'id': 'now', 'frames': [self.main_frame],
                          'pagesize': kw['pagesize']}
        page_template = PageTemplate(**template_attrs)
        self.platypus_header_calculate = False
        self.platypus_header_height = None
        self.platypus_footer = None
        self.context = context
        self.addPageTemplates([page_template])
        self.toc_high_level = self.context.toc_high_level

        self.frame_attr = {'leftPadding': 0, 'bottomPadding': 6,
                           'rightPadding': 0, 'topPadding': 6,
                           'showBoundary': 0}
        self.context = context
        # calculate width available
        self.width_available = self.width
        self.width_available -= self.frame_attr['leftPadding']
        self.width_available -= self.frame_attr['rightPadding']


    def beforePage(self):
        self.context.current_page += 1
        if self.context.has_header():
            # HEADER
            header = self.context.get_header()
            self.canv.saveState()

            # calculate height
            if self.platypus_header_calculate is False:
                element = header[0]
                height = element.wrap(self.width_available, self.pagesize[1])[1]
                height += self.frame_attr['topPadding']
                height += self.frame_attr['bottomPadding']
                self.platypus_header_height = height

            height = self.platypus_header_height
            # calculate coordinates
            x = self.leftMargin
            y = self.pagesize[1] - height

            # resize margin if the frame is too big
            if self.platypus_header_calculate is False:
                if self.topMargin < height:
                    self.platypus_header_calculate = True
                    self.topMargin = height
                    # calculate self.width and self.height
                    self._calc()
                    # reset the main frame with new margin
                    self.main_frame_attr['x1'] = self.leftMargin
                    self.main_frame_attr['y1'] = self.bottomMargin
                    self.main_frame_attr['width'] = self.width
                    self.main_frame_attr['height'] = self.height
                    self.main_frame.__init__(**self.main_frame_attr)
                else:
                    # frame is centered in top margin
                    y -= (self.topMargin - height) / 2
            else:
                # frame is centered in top margin
                y -= (self.topMargin - height) / 2

            # create a frame which will contain all platypus objects defined
            # in the footer
            fh = Frame(x, y, self.width_available, height, **self.frame_attr)
            fh.addFromList(self.context.get_header_copy(), self.canv)
            self.canv.restoreState()

        if self.context.has_footer():
            # FOOTER
            footer = self.context.get_footer()
            self.canv.saveState()

            # calculate height
            element = footer[0]
            height = element.wrap(self.width_available, self.pagesize[1])[1]
            height += self.frame_attr['topPadding']
            height += self.frame_attr['bottomPadding']

            # calculate coordinates
            x = self.leftMargin
            y = 0

            # resize margin if the frame is too big
            if self.bottomMargin < height:
                self.bottomMargin = height
                # calculate self.width and self.height
                self._calc()
                # reset the main frame with new margin
                self.main_frame_attr['x1'] = self.leftMargin
                self.main_frame_attr['y1'] = self.bottomMargin
                self.main_frame_attr['width'] = self.width
                self.main_frame_attr['height'] = self.height
                self.main_frame.__init__(**self.main_frame_attr)
            else:
                # frame is centered in bottom margin
                y = (self.bottomMargin - height) / 2

            # create a frame which will contain all platypus objects defined
            # in the footer
            ff = Frame(x, y, self.width_available, height, **self.frame_attr)
            ff.addFromList(self.context.get_footer_copy(), self.canv)
            self.canv.restoreState()



class MyDocTemplate(MySimpleDocTemplate):
    """
        The document template used for all PDF documents.
    """


    def _get_heading_level(self, name):
        if name.startswith('Heading'):
            return int(name[7:])
            # Heading0 -> h1
        elif name[0] == 'h' and len(name) == 2:
            # h1~h6
            return int(name[1:]) - 1
        else:
            return None


    def _allSatisfied(self):
        status = BaseDocTemplate._allSatisfied(self)
        if self.context.current_page != self.context.number_of_pages:
            status = 0
        self.context.number_of_pages = self.context.current_page
        self.context.current_page = 0
        self.toc_index = 0
        return status


    def afterFlowable(self, flowable):
        "Registers TOC entries and makes outline entries."

        if flowable.__class__.__name__ == 'Paragraph':
            style_name = flowable.style.name
            level = self._get_heading_level(style_name)
            if level is not None and level < self.toc_high_level:
                # Register TOC entries.
                text = flowable.getPlainText()
                pageNum = self.page
                # Hook the text content by adding a link
                content = '<para><a href="toc_%s">%s</a></para>'
                content = content % (self.toc_index, text)
                self.toc_index += 1
                self.notify('TOCEntry', (level, content, pageNum))

                # Add PDF outline entries (not really needed/tested here).
                key = str(hash(flowable))
                c = self.canv
                c.bookmarkPage(key)
                c.addOutlineEntry(text, key, level=level, closed=0)
