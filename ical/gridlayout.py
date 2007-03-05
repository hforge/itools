# -*- coding: UTF-8 -*-
# Copyright (C) 2000-2002 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#               2007 Nicolas Deram <nderam@itaapy.com>
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

# Import from Standard Library
from datetime import timedelta

# Import from itools
from itools.datatypes.datetime_ import ISOCalendarDate as Date
from itools.stl import stl
from itools.xhtml.XHTML import Document


template_string = """
  <td colspan="${cell/colspan}" rowspan="${cell/rowspan}" 
      class="event">
      <a stl:if="cell/newurl" class="add_event"
         href="${cell/newurl}">
        <img width="16" height="16" src="${add_icon}" />
      </a>
      <a href="${cell/content/url}">
        <div class="summary">${cell/content/SUMMARY}</div>
        <div stl:if="cell/content/ORGANIZER" class="organizer">
          ${cell/content/ORGANIZER}</div>
        <div stl:if="cell/content/TIME" class="time">
          (${cell/content/TIME})</div>
      </a>
  </td>
"""


template = Document()
template.load_state_from_string(template_string)
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
    """
    new, busy, free = 0, 1, 2

    def __init__(self, type, content=None, start=None, end=None, rowspan=None,
                 colspan=None):
        self.type = type
        self.content = content
        self.start = start
        self.end = end
        self.rowspan = rowspan
        self.colspan = colspan


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
        for name in ('content', 'rowspan', 'colspan'):
            namespace[name] = getattr(self, name)
        return namespace



class Row:

    def __init__(self):
        self.cells = []

    def __getitem__(self, i):
        return self.cells[i]

    def __setitem__(self, i, x):
        self.cells[i] = x

    def __len__(self):
        return len(self.cells)

    def append(self, x):
        self.cells.append(x)



class TimeGrid:

    def __init__(self):
      self.items = []

    def __getitem__(self, i):
      return self.items[i]

    def __len__(self):
      return len(self.items)

    def set(self, start, end, item):
      for i in range(len(self.items)):
        istart, iend, iitem = self.items[i]
        if start < istart or (start == istart and end <= iend):
          index = i
          break
      else:
        index = len(self.items)
      self.items.insert(index, (start, end, item))


    def render(self, times):
        nitems, iitems = len(self.items), 0
        # blocks = [(nrows, ncols), ..]
        blocks = []
        nrows = 0
        table = []
        state = []
        for time in times[:-1]:
            row = Row()
            table.append(row)

            ################################################################
            # add the busy cells
            for rowspan in state:
                if rowspan > 0:
                    row.append(Cell(Cell.busy))
                else:
                    row.append(Cell(Cell.free, content={'start': 
                                                        Time.encode(time)}))

            ################################################################
            # add new cells
            irow = 0
            while iitems < nitems:
              start, end, item = self.items[iitems]
              if start == time:
                  # look for a free cell
                  while irow < len(row):
                      if row[irow].type == Cell.free:
                          break
                      irow = irow + 1

                  # add cell
                  rowspan = times.index(end) - times.index(start)
                  cell = Cell(Cell.new, item, start, end, rowspan)
                  if irow >= len(row):
                      state.append(rowspan)
                      row.append(cell)
                  else:
                      state[irow] = rowspan
                      row[irow] = cell

                  # next item
                  iitems = iitems + 1
              else:
                  break

            ncols = len(row)
            # empty row?
            if ncols == 0:
                row.append(Cell(Cell.free, content={'start':
                                                    Time.encode(time)}))

            # next row, reduce the current rowspans
            nrows = nrows + 1
            for i in range(ncols):
                rowspan = state[i]
                if rowspan > 0:
                    state[i] = rowspan - 1

            # a new block?
            if state.count(0) == ncols:
                state = []
                blocks.append((nrows, ncols))
                nrows = 0

        # calculate the number of columns
        total_ncols = mcm(map(lambda x: x[1], blocks))

        # add colspan to each row and fill the incomplete rows with free cells
        base = 0
        for nrows, ncols in blocks:
            try:
                colspan = total_ncols/ncols
            except ZeroDivisionError:
                colspan = total_ncols
            irow = 0

            while irow < nrows:
                row = table[base + irow]
                row.colspan = colspan
                icol = len(row)
                while icol < ncols:
                    start = Time.encode(times[base+irow])
                    row.append(Cell(Cell.free, content={'start': start}))
                    icol = icol + 1
                irow = irow + 1
            base = base + nrows

        ####################################################################
        # FOR EACH ROW
        for index, row in enumerate(table):
            i = 0

            # FOR EACH CELL
            while i<len(row.cells):
                cell = row.cells[i]

                ########################################################
                #   EXTEND FREE CELL
                if cell.type == Cell.free:
                    j = i + 1
                    while j<len(row.cells) and row.cells[j].type==Cell.free:
                        row.cells[j].type = Cell.busy
                        j = j + 1
                    if j-i > 1:
                        cell.colspan = j - i
                    i = j

                ########################################################
                #   EXTEND NEW CELL
                elif cell.type == Cell.new:
                    new_extended = []
                    colspan = len(row.cells) - i

                    # MAX COLSPAN REACHED ( = 1)
                    if colspan <= 1:
                        break

                    # FOR EACH LINE BELOW, USED FOR CELL TO EXTEND
                    for n in range(cell.rowspan):
                        if colspan <= 1:
                            break

                        # GET CURRENT TESTED ROW
                        row_index = index+n
                        irow = table[row_index] 

                        # REDUCE max colspan if necessary
                        ilen = len(irow)
                        if ilen < colspan:
                            colspan = ilen

                        # TRY TO EXTEND
                        k = 1
                        while k < colspan:
                            if irow.cells[i+k].type != Cell.free:
                                colspan = k
                                break
                            k = k + 1
                        new_extended.append((row_index, i))

                    if colspan > 1:
                        for row_index, k in new_extended:
                            table[row_index].cells[k].colspan = colspan
                             
                            for col in range(1, colspan):
                                table[row_index].cells[k+col].type = Cell.busy
                        i = i + colspan
                    else:
                        i = i + 1

                # end
                else:
                    i = i + 1
                    
        return table, total_ncols


    def render_namespace(self, times):
        table, total_ncols = self.render(times)

        url = ';edit_event_form?method=grid_weekly_view&'
        ns_rows = []
        for row in table:
            ns_cells = []
            for cell in row.cells:
                # Don't add busy cells as they don't appear in template
                if cell.type == Cell.busy:
                    continue

                if cell.colspan is None:
                    cell.colspan = row.colspan

                ns_cell = cell.to_dict()

                # Add start time to url used to add events
                new_url = None
                if cell.content and 'start' in cell.content:
                    new_url = '%sstart=%s' % (url, cell.content['start'])
                ns_cell['newurl'] = new_url 

                ns_cells.append(ns_cell)

            ns_rows.append({'cells': ns_cells, 'colspan': row.colspan})

        return ns_rows, total_ncols



class TimeGridsCollection:

    def __init__(self, time_grids, headers, times, full_day_events,
                 start_date=None):
        if filter(lambda x: x, full_day_events):
            full_day = []
        else:
            full_day = None

        if headers is None:
            self.headers = None
        else:
            self.headers = []

        cols = []
        if start_date:
            current_date = start_date
        for i in range(len(time_grids)):
            table, ncols = time_grids[i].render_namespace(times)
            if headers is not None:
                self.headers.append({'header': headers[i], 'width': ncols})

            if full_day is not None:
                full_day.append({'events': full_day_events[i], 'width': ncols})

            # Add date to newurl for each cell having this parameter
            # Build namespace for the content of cells containing event (new)
            if start_date:
                for column in table:
                    str_date = Date.encode(current_date)
                    for cell in column['cells']:
                        if 'newurl' in cell:
                            url = '%s&date=%s' % (cell['newurl'], str_date)
                            cell['newurl'] = url
                        if cell['new']:
                            cell['ns'] = stl(template, {'cell': cell,
                                                         'add_icon': icon_path})

                current_date = current_date + timedelta(1)

            cols.append(table)

        self.full_day_events = full_day


        self.body = []
        for i in range(len(times)-1):
            items = []
            for col in cols:
                items.append(col[i])
            self.body.append({'start': Time.encode(times[i]),
                              'end': Time.encode(times[i+1]),
                              'items': items})


    def to_dict(self):
        namespace = {}
        namespace['headers'] = self.headers
        namespace['body'] = self.body
        namespace['full_day_events'] = self.full_day_events
        return namespace



def get_data(data, grid, start_date=None):
    # Build grid with Time objects
    grid = [ Time.decode(x) for x in grid ]

    # Build..
    headers = []
    events_with_time = []
    events_without_time = []
    for column in data:
        # Initialize
        time_grid = TimeGrid()
        full_day = []

        # Get the headers
        header = column.get('header')
        headers.append(header)

        # Get the events
        events = column['events']

        # Build the time grid
        for event in events:
            # Get the start and end times
            start = event['start']
            end = event['end']            

            # Put the event in the right place
            try:
                start, end = Time.decode(start), Time.decode(end)
            except:
                full_day.append(event)
            else:
                time_grid.set(start, end, event)

                # Fix grid if needed
                if start not in grid:
                    grid.append(start)
                if end not in grid:
                    grid.append(end)

        # Finalize
        events_with_time.append(time_grid)
        events_without_time.append(full_day)

    # Sort the grid
    grid.sort()

    return TimeGridsCollection(events_with_time, headers, grid, 
                               events_without_time, start_date).to_dict()

