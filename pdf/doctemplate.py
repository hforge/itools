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



class MySimpleDocTemplate(SimpleDocTemplate):
    def __init__(self, filename, context, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)
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
        if self.context.header:
            self.context.header = [Table([[self.context.header]])]
            # HEADER
            self.canv.saveState()

            # calculate height
            element = self.context.header[0]
            height = element.wrap(self.width_available, self.pagesize[1])[1]
            height += self.frame_attr['topPadding']
            height += self.frame_attr['bottomPadding']

            # calculate coordinates
            x = self.leftMargin
            y = self.pagesize[1] - height

            # resize margin if the frame is too big
            if self.topMargin < height:
                self.topMargin = height
            else:
                # frame is centered in top margin
                y -= (self.topMargin - height) / 2

            # create a frame which will contain all platypus objects defined
            # in the footer
            fh = Frame(x, y, self.width_available, height, **self.frame_attr)
            fh.addFromList(copy.deepcopy(self.context.header), self.canv)
            self.canv.restoreState()

        if self.context.footer:
            self.context.footer = [Table([[self.context.footer]])]
            # FOOTER
            self.canv.saveState()

            # calculate height
            element = self.context.footer[0]
            height = element.wrap(self.width_available, self.pagesize[1])[1]
            height += self.frame_attr['topPadding']
            height += self.frame_attr['bottomPadding']

            # calculate coordinates
            x = self.leftMargin
            y = 0

            # resize margin if the frame is too big
            if self.bottomMargin < height:
                self.bottomMargin = height
            else:
                # frame is centered in bottom margin
                y = (self.bottomMargin - height) / 2

            # create a frame which will contain all platypus objects defined
            # in the footer
            ff = Frame(x, y, self.width_available, height, **self.frame_attr)
            ff.addFromList(copy.deepcopy(self.context.footer), self.canv)
            self.canv.restoreState()



class MyDocTemplate(BaseDocTemplate):
    """
        The document template used for all PDF documents.
    """


    def __init__(self, filename, context, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)
        self.toc_index = 0
        frame1 = Frame(self.leftMargin, self.bottomMargin, self.width,
                       self.height, id='normal')
        template_attrs = {'id': 'now', 'frames': [frame1],
                          'pagesize': kw['pagesize']}
        page_template = PageTemplate(**template_attrs)
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


    def beforePage(self):
        self.context.current_page += 1
        if self.context.header:
            self.context.header = [Table([[self.context.header]])]
            # HEADER
            self.canv.saveState()

            # calculate height
            element = self.context.header[0]
            height = element.wrap(self.width_available, self.pagesize[1])[1]
            height += self.frame_attr['topPadding']
            height += self.frame_attr['bottomPadding']

            # calculate coordinates
            x = self.leftMargin
            y = self.pagesize[1] - height

            # resize margin if the frame is too big
            if self.topMargin < height:
                self.topMargin = height
            else:
                # frame is centered in top margin
                y -= (self.topMargin - height) / 2

            # create a frame which will contain all platypus objects defined
            # in the footer
            fh = Frame(x, y, self.width_available, height, **self.frame_attr)
            fh.addFromList(copy.deepcopy(self.context.header), self.canv)
            self.canv.restoreState()

        if self.context.footer and self.platypus_footer is None:
            self.platypus_footer = [Table([[self.context.footer]])]

        if self.platypus_footer is not None:
            # FOOTER
            self.canv.saveState()

            # calculate height
            element = self.platypus_footer[0]
            height = element.wrap(self.width_available, self.pagesize[1])[1]
            height += self.frame_attr['topPadding']
            height += self.frame_attr['bottomPadding']

            # calculate coordinates
            x = self.leftMargin
            y = 0

            # resize margin if the frame is too big
            if self.bottomMargin < height:
                self.bottomMargin = height
            else:
                # frame is centered in bottom margin
                y = (self.bottomMargin - height) / 2

            # create a frame which will contain all platypus objects defined
            # in the footer
            ff = Frame(x, y, self.width_available, height, **self.frame_attr)
            footer = self.context.footer
            copy_footer = copy.deepcopy(footer)
            ff.addFromList(copy_footer, self.canv)
            self.canv.restoreState()
