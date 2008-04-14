# -*- coding: UTF-8 -*-
# Copyright (C) 2002, 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Nicolas Deram <nicolas@itaapy.com>
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

# Import from Standard Library
from datetime import date, timedelta

# Import from itools
from itools.datatypes import Date
from itools.stl import stl
from itools.html import XHTMLFile


# Template to display full day events
template_string = """
  <td class="color${event/cal}">
    <a href="${event/url}" class="${event/STATUS}">${event/SUMMARY}</a>
  </td>
"""
default_template_fd = XHTMLFile()
default_template_fd.load_state_from_string(template_string)

# Template to display events with timetables
template_string = """
  <td colspan="${cell/colspan}" rowspan="${cell/rowspan}"
    valign="top" class="color${cell/content/cal}">
      <a xmlns:stl="http://xml.itools.org/namespaces/stl"
        stl:if="cell/newurl" class="add_event" href="${cell/newurl}">
        <img width="16" height="16" src="${add_icon}" />
      </a><br/>
      <a href="${cell/content/url}" class="${cell/content/STATUS}">
        <span class="summary">${cell/content/SUMMARY}</span>
      </a>
  </td>
"""
default_template = XHTMLFile()
default_template.load_state_from_string(template_string)
icon_path = '/ui/images/button_add.png'


def mcm(l):
    """
    Calculates the minimum common multiple of a list of integers.
    """

    if len(l) == 0:
        return 0

    l.sort()
    l.reverse()
    x = l[0]
    if x == 0:
        x = 1
    for y in l[1:]:
        if y==0:
            y = 1
        # Which is the maximum and which is hte minimum?
        maximum = max(x, y)
        minimum = min(x, y)
        # Calculate the maximum common factor (mcf)
        mod = maximum % minimum
        while mod:
            maximum = minimum
            minimum = mod
            mod = maximum % minimum
        mcf = minimum
        # Calculate the mcm
        x = mcf*(x/mcf)*(y/mcf)
    return x



class Time(object):
    """
    This class represents a positive amount of time with a precision of
    minutes. Internally time is represented as a pair of values, hours
    and minutes.
    """

    @staticmethod
    def decode(time):
        """
        The constructor takes an string with the format "hh:mm", it
        parses the string and internally stores the hours and minutes
        as a tuple of integers.
        """
        x = time.split(':')

        if len(x) != 2:
            raise ValueError, time

        return int(x[0]), int(x[1])

    @staticmethod
    def encode(value):
        """
        Textual representation of a Time object, it's "hh:mm".
        """
        return "%02d:%02d" % value



class Cell(object):
    """
    Class which represents a cell in the table.

    A cell can be:
      - new: the start of an event
      - busy: part of an event (hidden)
      - free: free cell

    It can have the attributes:
      - content:
      - start:
      - end:
      - rowspan:
      - colspan:
      - cal: resource_name
    """
    new, busy, free = 0, 1, 2

    def __init__(self, type, content=None, start=None, end=None, rowspan=None,
                 colspan=None, cal=None):
        self.type = type
        self.content = content
        self.start = start
        self.end = end
        self.rowspan = rowspan
        self.colspan = colspan
        self.cal = cal


    def to_dict(self):
        namespace = {}
        namespace['new'] = self.type == Cell.new
        namespace['busy'] = self.type == Cell.busy
        namespace['free'] = self.type == Cell.free
        namespace['start'] = namespace['end'] = None
        if self.start:
            namespace['start'] = Time.encode(self.start)
        if self.end:
            namespace['end'] = Time.encode(self.end)
        for name in ('content', 'rowspan', 'colspan', 'cal'):
            namespace[name] = getattr(self, name)
        return namespace



def insert_item(items, start, end, item, cal):
    for i, (istart, iend, iitem, ical) in enumerate(items):
        if start < istart or (start == istart and end <= iend):
            index = i
            break
    else:
        index = len(items)
    items.insert(index, (start, end, item, cal))


def render_namespace(items, times, with_new_url):
    nitems, iitems = len(items), 0
    # blocks = [(nrows, ncols), ..]
    blocks, table, state = [], [], []
    nrows = 0
    for itime, time in enumerate(times[:-1]):
        cells = []

        tt_end = times[itime + 1]
        # add the busy cells
        for rowspan in state:
            if rowspan > 0:
                cells.append(Cell(Cell.busy, colspan=1))
            else:
                cells.append(Cell(Cell.free, start=time, end=tt_end))

        # add new cells
        icell = 0
        while iitems < nitems:
            start, end, item, cal = items[iitems]
            if start != time:
                break
            # look for a free cell
            while icell < len(cells):
                if cells[icell].type == Cell.free:
                    break
                icell = icell + 1
            # add cell
            rowspan = times.index(end) - times.index(start)
            cell = Cell(Cell.new, item, start, end, rowspan, 1, cal)
            if icell >= len(cells):
                state.append(rowspan)
                cells.append(cell)
            else:
                state[icell] = rowspan
                cells[icell] = cell
            # next item
            iitems = iitems + 1

        ncols = len(cells)
        # empty row?
        if ncols == 0:
            cells.append(Cell(Cell.free, start=time, end=tt_end))

        # next row, reduce the current rowspans
        nrows = nrows + 1
        for i in range(ncols):
            rowspan = state[i]
            if rowspan > 0:
                state[i] = rowspan - 1

        # a new block?
        state_0_count = state.count(0)
        if state_0_count == ncols:
            state = []
            blocks.append((nrows, ncols))
            nrows = 0

        # Add current row cells to table
        table.append(cells)

    # calculate the number of columns
    total_ncols = mcm(map(lambda x: x[1], blocks))

    # add colspan to each row and fill the incomplete rows with free cells
    base = 0
    for nrows, ncols in blocks:
        if ncols != 0:
            b_colspan = total_ncols/ncols
        else:
            b_colspan = total_ncols

        for irow in range(nrows):
            cells = table[base + irow]
            for cell in cells:
                cell.colspan = b_colspan
            for icol in range(len(cells), ncols):
                cells.append(Cell(Cell.free, start=times[base+irow],
                                  colspan=b_colspan))
            table[base + irow] = cells
        base = base + nrows

    ####################################################################
    # FOR EACH ROW
    for index, row_cells in enumerate(table):
        new_cells, free_cells = [], []
        for cell in row_cells:
            if cell.type == Cell.new:
                new_cells.append(cell)
            elif cell.type == Cell.free:
                free_cells.append(cell)

        if free_cells == row_cells:
            continue

        # Try to extend colspan of new cells
        #   (checking the cells below in rowspan)
        for cell in new_cells:
            colspan = cell.colspan
            if colspan <= 1:
                continue

            # FOR EACH LINE BELOW, USED FOR CELL TO EXTEND
            new_extended = []
            for n in range(cell.rowspan):
                if colspan <= 1:
                    break
                # GET CURRENT TESTED ROW
                row_index = index + n
                icells = table[row_index]
                # REDUCE max colspan if necessary
                ilen = len(icells)
                if ilen < colspan:
                    colspan = ilen
                # TRY TO EXTEND
                i = row_cells.index(cell)
                k = 0
                while k < colspan and (i+k) < ilen:
                    if icells[i+k].type != Cell.free:
                        colspan = k
                        break
                    k = k + 1
                new_extended.append((row_index, i))

            # Update cells below
            if colspan > 1:
                for row_index, i in new_extended:
                    c_colspan = colspan
                    c_row = table[row_index]
                    l_c_row = len(c_row)
                    for col in range(i+1, i+colspan):
                        if col < l_c_row:
                            current_cell = c_row[col]
                            free_cells.remove(current_cell)
                            current_cell.type = Cell.busy
                            c_colspan = c_colspan + current_cell.colspan
                    current_cell[i].colspan = c_colspan

        # Collapse free cells
        l_row_cells = len(row_cells)
        for icell, cell in enumerate(row_cells):
            if cell.type == Cell.free:
                jcelltest = icell + 1
                start = cell.start
                while jcelltest < l_row_cells:
                    if jcelltest != icell:
                        celltest = row_cells[jcelltest]
                        if celltest.type != Cell.free:
                            break
                        if celltest.start == start:
                            celltest.type = Cell.busy
                            cell.colspan = cell.colspan + celltest.colspan
                    jcelltest = jcelltest + 1


    ######################################################################
    # render_namespace
    ######################################################################

    url = ';edit_event_form?method=weekly_view&'
    ns_rows = []
    for cells in table:
        ns_cells = []
        for cell in cells:
            # Don't add busy cells as they don't appear in template
            if cell.type == Cell.busy:
                continue
            ns_cell = cell.to_dict()
            new_url = None
            if with_new_url is True:
                # Add start time to url used to add events
                if cell.start:
                    new_url = '%sstart_time=%s' % (url, Time.encode(cell.start))
                if cell.end:
                    new_url = '%s&end_time=%s' %(new_url, Time.encode(cell.end))
            ns_cell['newurl'] = new_url
            ns_cells.append(ns_cell)
        ns_rows.append({'cells': ns_cells})

    return ns_rows, total_ncols


def get_grid_data(data, grid, start_date=None, templates=(None, None),
                  with_new_url=True):
    """
    Build final namespace from data and grid to be used in gridlayout
    templates.
    """
    template, template_fd = templates
    if template is None:
        template = default_template
    if template_fd is None:
        template_fd = default_template_fd
    # Build grid with Time objects
    grid = [ Time.decode(x) for x in grid ]

    # Build..
    headers, events_with_time, events_without_time = [], [], []
    for column in data:
        time_grid = []
        full_day = []

        events = column['events']
        # Build the time grid
        for event in events:
            start, end = event['start'], event['end']
            # Put the event in the right place
            if not event['TIME']:
                event['ns'] = stl(template_fd, event)
                full_day.append(event)
            else:
                start, end = Time.decode(start), Time.decode(end)
                insert_item(time_grid, start, end, event, event['cal'])

                # Fix grid if needed
                if start not in grid:
                    grid.append(start)
                if end not in grid:
                    grid.append(end)

        # Finalize
        headers.append(column.get('header'))
        events_with_time.append(time_grid)
        events_without_time.append(full_day)

    # Sort the grid
    grid.sort()

    ######################################################################
    # Build_timegrids_collection with given data:
    #   (events_with_time, headers, grid, events_without_time, start_date=None)
    today = date.today()
    if start_date:
        current_date = start_date

    ns_full_day = None
    if filter(lambda x: x, events_without_time):
        ns_full_day = []
    ns_headers = []

    cols = []
    for i in range(len(events_with_time)):
        table, ncols = render_namespace(events_with_time[i], grid, with_new_url)
        if headers is not None:
            if current_date == today:
                h_class = 'cal_day_selected'
            else:
                h_class = 'header'
            ns_headers.append({'header': headers[i], 'width': ncols,
                               'class': h_class})
        if ns_full_day is not None:
            ns_full_day.append({'events': events_without_time[i],
                                'width': ncols})

        # Add date to newurl for each cell having this parameter
        # Build namespace for the content of cells containing event (new)
        if start_date is not None:
            str_date = Date.encode(current_date)
            for column in table:
                for cell in column['cells']:
                    if cell['newurl'] is not None:
                        url = '%s&date=%s' % (cell['newurl'], str_date)
                        cell['newurl'] = url
                    if cell['new']:
                        cell['ns'] = stl(template, {'cell': cell,
                                                    'add_icon': icon_path})
            current_date = current_date + timedelta(1)
        cols.append(table)

    body = []
    for i in range(len(grid)-1):
        body.append({'start': Time.encode(grid[i]),
                     'end': Time.encode(grid[i+1]),
                     'items': [col[i] for col in cols]})

    namespace = {'headers': ns_headers, 'body': body,
                 'full_day_events': ns_full_day}
    return namespace
