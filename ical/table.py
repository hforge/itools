# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Nicolas Oyez <nicoyez@gmail.com>
# Copyright (C) 2005-2007 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2008 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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

# Import from Python Standard Library
from datetime import datetime, timedelta
from operator import itemgetter

# Import from itools
from itools.csv import parse_table, Property, Record as TableRecord, Table
from itools.datatypes import String, Unicode
from itools.handlers import merge_dics
from itools.xapian import EqQuery, RangeQuery, OrQuery, AndQuery
from base import BaseCalendar
from types import data_properties, Time


# The smallest possible difference between non-equal timedelta objects.
#
# XXX To be used to work-around the fact that range searches don't include
# the righ limit. So if we want to search a date between 'dtstart' and
# 'dtend', we must write:
#
#    RangeQuery('date', dtstart, dtend + resolution)
#
# To be used systematically. Till the day we replace range searches by the
# more complete set: GreaterThan, GreaterThanOrEqual, LesserThan and
# LesserThanOrEqual.
resolution = timedelta.resolution



class Record(TableRecord):
    """A Record with some icalendar specific methods in addition.
    """

    def get_version(self, sequence=None):
        """Return the last version of current component or the sequence's one.
        """
        if sequence is None:
            sequence = self[-1]
        for version in self:
            if self.get_property('SEQUENCE') == sequence:
                return version
        return None


    # Get a property of current component
    def get_property(self, name=None):
        """Return the value of given name property as a Property or as a list
        of Property objects if it can occur more than once.

        Return all property values as a dict {name: value, ...} where
        value is a Property or a list of Property objects if it can
        occur more than once.

        Note that it return values for the last version of this component.
        """
        if name:
            return TableRecord.get_property(self, name)
        return self[-1]


    def get_end(self):
        return self.get_property('DTEND').value


    def get_ns_event(self, day, resource_name=None, conflicts_list=[],
                     timetable=None, grid=False,
                     starts_on=True, ends_on=True, out_on=True):
        """Specify the namespace given on views to represent an event.

        day: date selected XXX not used for now
        conflicts_list: list of conflicting uids for current resource, [] if
            not used
        timetable: timetable index or None
        grid: current calculated view uses gridlayout
        starts_on, ends_on and out_on are used to adjust display.

        By default, we get:

          start: HH:MM, end: HH:MM,
            TIME: (HH:MM-HH:MM) or TIME: (HH:MM...) or TIME: (...HH:MM)
          or
          start: None,  end: None, TIME: None

          SUMMARY: 'summary of the event'
          STATUS: 'status' (class: cal_conflict, if id in conflicts_list)
          ORGANIZER: 'organizer of the event'

##          XXX url: url to access edit_event_form on current event
        """
        properties = self.get_property
        ns = {}
        ns['SUMMARY'] = properties('SUMMARY').value
        ns['ORGANIZER'] = properties('ORGANIZER').value

        ###############################################################
        # Set dtstart and dtend values using '...' for events which
        # appear into more than one cell
        start = properties('DTSTART')
        end = properties('DTEND')
        param = start.parameters
        ns['start'] = Time.encode(start.value.time())
        ns['end'] = Time.encode(end.value.time())
        ns['TIME'] = None
        if grid:
            # Neither a full day event nor a multiple days event
            if ('VALUE' not in param or 'DATE' not in param['VALUE']) \
              and start.value.date() == end.value.date():
                ns['TIME'] = '%s - %s' % (ns['start'], ns['end'])
            else:
                ns['start'] = ns['end'] = None
        elif not out_on:
            if 'VALUE' not in param or 'DATE' not in param['VALUE']:
                value = ''
                if starts_on:
                    value = ns['start']
                    if ends_on:
                        value = value + '-'
                    else:
                        value = value + '...'
                if ends_on:
                    value = value + ns['end']
                    if not starts_on:
                        value = '...' + value
                ns['TIME'] = '(' + value + ')'

        ###############################################################
        # Set class for conflicting events or just from status value
        id = self.id
        if id in conflicts_list:
            ns['STATUS'] = 'cal_conflict'
        else:
            ns['STATUS'] = ''
            status = properties('STATUS')
            if status:
                ns['STATUS'] = status.value

        if not resource_name:
            id = str(id)
        else:
            id = '%s/%s' % (resource_name, id)
        ns['id'] = id
#        resource =
#        # Set url to action like edit_event_form
#        url = resource_name.get_action_url(day=day)
#        if url:
#            url = '%s?id=%s' % (url, id)
#            if timetable:
#                url = '%s&timetable=%s' % (url, timetable)
#        ns['url'] = url

        return ns



class icalendarTable(BaseCalendar, Table):
    """An icalendarTable is a handler for calendar data, generally used as an
    ical file but here as a table object.
    """

    record_class = Record

    record_schema = merge_dics(
        data_properties,
        type=String(index='keyword'),
    )


    #########################################################################
    # API
    #########################################################################
    def load_state_from_ical_file(self, file):
        """Load state from the given ical file.
        """
        self.reset()
        self.set_changed()

        components = {}

        # Read the data
        data = file.read()

        # Parse
        lines = []
        for name, value, parameters in parse_table(data):
            # Timestamp (ts), Schema, or Something else
            datatype = self.get_datatype(name)
            value = datatype.decode(value)
            property = Property(value, parameters)
            # Append
            lines.append((name, property))

        # Read first line
        first = lines[0]
        if (first[0] != 'BEGIN' or first[1].value != 'VCALENDAR'
            or len(first[1].parameters) != 0):
            raise ValueError, 'icalendar must begin with BEGIN:VCALENDAR'

        lines = lines[1:]

        ###################################################################
        # Skip properties
        # TODO Currently tables are not able to handler global properties,
        # we must implement this feature to be able to load from ical files.
        n_line = 0
        for name, value in lines:
            if name == 'BEGIN':
                break
            elif name == 'END':
                break
            n_line += 1

        lines = lines[n_line:]

        ###################################################################
        # Read components
        c_type = None
        uid = None
        records = self.records
        id = 0
        uids = {}

        for prop_name, prop_value in lines[:-1]:
            if prop_name in ('PRODID', 'VERSION'):
                raise ValueError, 'PRODID and VERSION must appear before '\
                                  'any component'
            if c_type is None:
                if prop_name == 'BEGIN':
                    c_type = prop_value.value
                    c_properties = {}
                continue

            if prop_name == 'END':
                if prop_value.value == c_type:
                    if uid is None:
                        raise ValueError, 'UID is not present'

                    record = self.get_record(id) or Record(id)
                    c_properties['type'] = Property(c_type)
                    c_properties['UID'] = Property(uid)
                    sequence = c_properties.get('SEQUENCE', None)
                    c_properties['SEQUENCE'] = sequence or Property(0)
                    c_properties['ts'] = Property(datetime.now())
                    record.append(c_properties)
                    if uid in uids:
                        n = uids[uid] + 1
                        uids[uid] = n
                    else:
                        n = 0
                        uids[uid] = 0
                    self.added_records.append((id, n))
                    records.append(record)

                    # Next
                    c_type = None
                    uid = None
                    if n == 0:
                        id = id + 1
                #elif prop_value.value in component_list:
                #    raise ValueError, '%s component can NOT be inserted '\
                #          'into %s component' % (prop_value.value, c_type)
                else:
                    raise ValueError, 'Inner components are not managed yet'
            else:
                if prop_name == 'UID':
                    uid = prop_value.value
                else:
                    datatype = self.get_datatype(prop_name)

                    if getattr(datatype, 'multiple', False) is True:
                        value = c_properties.setdefault(prop_name, [])
                        value.append(prop_value)
                    else:
                        # Check the property has not yet being found
                        if prop_name in c_properties:
                            raise ValueError, \
                                  "property '%s' can occur only once" % name
                        # Set the property
                        c_properties[prop_name] = prop_value

        # Index the records
        for record in records:
            if record is not None:
                self.catalog.index_document(record, record.id)


    def to_ical(self):
        """Serialize as an ical file, generally named .ics
        """
        lines = []

        line = 'BEGIN:VCALENDAR\n'
        lines.append(Unicode.encode(line))

        # Calendar properties
        properties = (
            ('VERSION', u'2.0'),
            ('PRODID', u'-//itaapy.com/NONSGML ikaaro icalendar V1.0//EN'))
        for name, value in properties:
            value = Property(value)
            line = self.encode_property(name, value)
            lines.append(line[0])

        # Calendar components
        for record in self.records:
            if record is not None:
                seq = 0
                c_type = record.type
                for version in record:
                    line = 'BEGIN:%s\n' % c_type
                    lines.append(Unicode.encode(line))
                    # Properties
                    names = version.keys()
                    names.sort()
                    for name in names:
                        if name in ('id', 'ts', 'type'):
                            continue
                        elif name == 'DTSTAMP':
                            value = version['ts']
                        else:
                            value = version[name]
                        if name == 'SEQUENCE':
                            value.value += seq
                        name = name.upper()
                        line = self.encode_property(name, value)
                        lines.extend(line)
                    line = 'END:%s\n' % c_type
                    lines.append(Unicode.encode(line))
                    seq += 1

        line = 'END:VCALENDAR\n'
        lines.append(Unicode.encode(line))

        return ''.join(lines)


    def add_record(self, kw):
        if 'UID' not in kw:
            type = kw.get('type', 'UNKNOWN')
            kw['UID'] = self.generate_uid(type)

        id = len(self.records)
        record = Record(id)
        version = self.properties_to_dict(kw)
        version['ts'] = Property(datetime.now())
        record.append(version)
        # Change
        self.set_changed()
        self.added_records.append((id, 0))
        self.records.append(record)
        self.catalog.index_document(record, id)
        # Back
        return record


    def get_component_by_uid(self, uid):
        """Return components with the given uid, None if it doesn't appear.
        """
        return self.search(UID=uid)


    # Deprecated
    def get_components(self, type=None):
        """Return a dict {component_type: Record[], ...}
        or
        Return Record[] of given type.
        """
        if type is None:
            return self.records

        return self.search(type=type)


    # Get some events corresponding to arguments
    def search_events(self, subset=None, **kw):
        """Return a list of Record objects of type 'VEVENT' corresponding to
        the given filters.

        It should be used like this, for example:

            events = cal.search_events(
                STATUS='TENTATIVE',
                PRIORITY=1,
                ATTENDEE=[URI.decode('mailto:jdoe@itaapy.com'),
                          URI.decode('mailto:jsmith@itaapy.com')])

        ** With a list of values, events match if at least one value matches

        It searches into all components or in the provided subset list of
        components.
        """
        res_events = []

        # Get the list of differents property names used to filter
        filters = kw.keys()

        # For each event
        events = subset or self.search(type='VEVENT')
        for event in events:
            if event in res_events:
                continue
            version = self.get_record(id=event.id)[-1]

            # For each filter
            for filter in filters:
                # If filter not in component, go to next one
                if filter not in version:
                    break
                # Test filter
                expected = kw.get(filter)
                value = version[filter]
                datatype = self.get_datatype(filter)

                if getattr(datatype, 'multiple', False) is True:
                    value = [ isinstance(x, Property) and x or Property(x)
                              for x in value ]
                    if not isinstance(expected, list):
                        expected = [expected, ]
                    for item in value:
                        if item.value in expected:
                            break
                        elif item.value == expected:
                            break
                    else:
                        break
                else:
                    if not isinstance(value, Property):
                        value = Property(value)
                    if value.value != expected:
                        break
            else:
                res_events.append(event)
        return res_events


    def search_events_in_range(self, dtstart, dtend, sortby=None, **kw):
        """Return a list of Records objects of type 'VEVENT' matching the
        given dates range and sorted if requested.  If kw is filled, it calls
        search_events on the found subset to return only components matching
        filters.

        RangeSearch is [left, right[
        """
        # Check type of dates, we need datetime for method in_range
        if not isinstance(dtstart, datetime):
            dtstart = datetime(dtstart.year, dtstart.month, dtstart.day)
        if not isinstance(dtend, datetime):
            dtend = datetime(dtend.year, dtend.month, dtend.day)
            # dtend is include into range
            dtend = dtend + timedelta(days=1) - resolution

        # Get only the events which matches
        dtstart_limit = str(dtstart + resolution)
        dtend_limit = str(dtend + resolution)
        dtstart = str(dtstart)
        dtend = str(dtend)
        query = AndQuery(
            EqQuery('type', 'VEVENT'),
            OrQuery(RangeQuery('DTSTART', dtstart, dtend),
                    RangeQuery('DTEND', dtstart_limit, dtend_limit),
                    AndQuery(RangeQuery('DTSTART', None, dtstart),
                             RangeQuery('DTEND', dtend, None))))
        results = self.search(query)

        if results == []:
            return []

        # Check filters
        if kw:
            results = self.search_events(subset=results, **kw)

        # Nothing to sort or inactive
        if sortby is None or len(results) <= 1:
            return results

        # Get results as a dict to sort them
        res_events = []
        for event in results:
            version = event[-1]
            value = {
                'dtstart': version['DTSTART'].value,
                'dtend': version['DTEND'].value,
                'event': event
              }
            res_events.append(value)
        # Sort by dtstart
        res_events = sorted(res_events, key=itemgetter('dtstart'))
        # Sort by dtend
        res = []
        current = [res_events[0]]
        for e in res_events[1:]:
            if e['dtstart'] == current[0]['dtstart']:
                current.append(e)
            else:
                res.extend(x['event']
                           for x in sorted(current, key=itemgetter('dtend')))
                current = [e]
        res.extend(x['event'] for x in sorted(current,
                                              key=itemgetter('dtend')))
        return res


    def search_events_in_date(self, selected_date, sortby=None, **kw):
        """Return a list of Component objects of type 'VEVENT' matching the
        given date and sorted if requested.
        """
        dtstart = datetime(selected_date.year, selected_date.month,
                           selected_date.day)
        dtend = dtstart + timedelta(days=1) - resolution
        return self.search_events_in_range(dtstart, dtend, sortby=sortby, **kw)


    # Test if any event corresponds to a given date
    def has_event_in_date(self, date):
        """Return True if there is at least one event matching the given date.
        """
        return self.search_events_in_date(date) != []


    def get_conflicts(self, start_date, end_date=None):
        """Returns a list of uid couples which happen at the same time.
        We check only last occurrence of events.
        """
        if end_date is not None:
            events = self.search_events_in_range(start_date, end_date)
        else:
            events = self.search_events_in_date(start_date)
        if len(events) <= 1:
            return None

        conflicts = []
        # We take each event as a reference
        for i, event_ref in enumerate(events):
            version = event_ref[-1]
            dtstart_ref = version['DTSTART'].value
            dtend_ref = version['DTEND'].value
            # For each other event, we test if there is a conflict
            for j, event in enumerate(events):
                if j <= i:
                    continue
                version = event[-1]
                dtstart = version['DTSTART'].value
                dtend = version['DTEND'].value

                if dtstart >=  dtend_ref or dtend <= dtstart_ref:
                    continue
                conflicts.append((i, j))

        # Replace index of components by their UID
        if conflicts != []:
            for index, (i, j) in enumerate(conflicts):
                conflicts[index] = (events[i].id, events[j].id)

        return conflicts

