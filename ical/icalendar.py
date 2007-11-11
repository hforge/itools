# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Nicolas Oyez <nicoyez@gmail.com>
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2005-2007 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
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
from itools.datatypes import Integer, String, Unicode, URI
from itools.catalog import (PhraseQuery, EqQuery, RangeQuery, OrQuery,
        AndQuery, KeywordField, MemoryCatalog)
from itools.handlers import Text, parse_table, fold_line, escape_data
from itools.handlers import Table, Record as TableRecord, Property
from types import data_properties, DateTime, Time


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


class PropertyValue(object):
    """
    PropertyValue handles a property value and parameters.

    Parameters are a dict containing list of values:
        {param1_name: [param_values], ...}
    """

    def __init__(self, value, **kw):
        self.value = value
        self.parameters = kw


class Component(object):
    """
    Parses and evaluates a component block.

        input :   string values for c_type and uid
                  a list of Property objects
                  (Property objects can share the same name as a property
                  name can appear more than one time in a component)

        output :  unchanged c_type and uid
                  a dictionnary of versions of this component including
                  a dict {'property_name': PropertyValue[] } for properties
    """
    # XXX A parse method should be added to test properties inside of current
    # component-type/properties (for example to test if property can appear
    # more than one time, ...)

    def __init__(self, c_type, uid):
        """
        Initialize the component.

        c_type -- type of component as a string (i.e. 'VEVENT')
        """
        self.c_type = c_type
        self.uid = uid
        self.versions = {}


    #######################################################################
    # API / Private
    #######################################################################
    def get_value(self, name):
        """
        Returns the value of a property if it exists. Otherwise returns None.
        """
        # Case insensitive
        name = name.upper()

        # The type
        if name == 'TYPE':
            return self.c_type

        # Get the last version
        version = self.get_version()

        # Properties
        if name not in version:
            return None

        # According to the RFC, when DTEND is of format DATE, it is
        # interpreted as the event happens the whole day.
        if name == 'DTEND' and 'DTEND' not in version:
            value = version['DTSTART'].value + timedelta(days=1) - resolution
        else:
            property = version[name]
            value = property.value

        return value


    def get_sequences(self):
        sequences = self.versions.keys()
        sequences.sort()
        return sequences


    def add_version(self, properties):
        # Sequence in properties only if just loading file
        if 'SEQUENCE' in properties:
            sequence = properties.pop('SEQUENCE')
            sequence = sequence.value
        else:
            sequences = self.get_sequences()
            if sequences:
                sequence = sequences[-1] + 1
            else:
                sequence = 0

        # Timestamp
        if 'DTSTAMP' not in properties:
            properties['DTSTAMP'] = PropertyValue(datetime.today())

        self.versions[sequence] = properties


    #######################################################################
    # API / Public
    #######################################################################
    def get_version(self, sequence=None):
        """
        Return the last version of current component or the sequence's one.
        """
        if sequence is None:
            sequence = self.get_sequences()[-1]
        return self.versions[sequence]


    # Get a property of current component
    def get_property(self, name=None):
        """
        Return the value of given name property as a PropertyValue or as a list
        of PropertyValue objects if it can occur more than once.

        Return icalendar property values as a dict {name: value, ...} where
        value is a PropertyValue or a list of PropertyValue objects if it can
        occur more than once.

        Note that it return values for the last version of this component.
        """
        version = self.get_version()
        if name:
            return version.get(name, None)
        return version

    get_property_values = get_property


    def get_end(self):
        return self.get_property('DTEND').value


    def get_ns_event(self, day, resource_name=None, conflicts_list=[],
                     timetable=None, grid=False,
                     starts_on=True, ends_on=True, out_on=True):
        """
        Specify the namespace given on views to represent an event.

        day: date selected XXX not used for now
        conflicts_list: list of conflicts for current resource, [] if not used
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
        id = self.uid
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
        # Set url to action like edit_event_form
#        url = resource_name.get_action_url(day=day)
#        if url:
#            url = '%s?id=%s' % (url, id)
#            if timetable:
#                url = '%s&timetable=%s' % (url, timetable)
#        ns['url'] = url

        return ns



class icalendar(Text):
    """
    icalendar structure :

        BEGIN:VCALENDAR

            --properties
                     required : PRODID, VERSION
                     optionnal : CALSCALE, METHOD, non-standard ones...

            --components(min:1)
                     VEVENT, TODO, JOURNAL, FREEBUSY, TIMEZONE,
                     iana component, non-standard component...

        END:VCALENDAR
    """

    __slots__ = ['database', 'uri', 'timestamp', 'dirty',
                 'properties', 'components', 'catalog', 'encoding']
    class_mimetypes = ['text/calendar']
    class_extension = 'ics'


    # To override a component property from the spec, or to add a new one,
    # define this class variable.
    schema = {
##        'DTSTART': DateTime(occurs=1, index='keyword'),
##        'DTEND': DateTime(occurs=1, index='keyword'),
    }


    @classmethod
    def get_datatype(cls, name):
        # Overriden schema
        if name in cls.schema:
            return cls.schema[name]
        # The specs schema
        if name in data_properties:
            return data_properties[name]
        # Default
        return String(occurs=0)


    #########################################################################
    # New
    #########################################################################
    def _init_ical(self):
        self.properties = {}
        self.components = {}
        self.catalog = MemoryCatalog()
        self.catalog.add_index('type', KeywordField)
        self.catalog.add_index('dtstart', KeywordField)
        self.catalog.add_index('dtend', KeywordField)


    def new(self):
        self._init_ical()

        properties = (
            ('VERSION', {}, u'2.0'),
            ('PRODID', {}, u'-//itaapy.com/NONSGML ikaaro icalendar V1.0//EN')
          )
        for name, param, value in properties:
            self.properties[name] = PropertyValue(value, **param)

        # The encoding
        self.encoding = 'UTF-8'


    #########################################################################
    # Load State
    #########################################################################
    def _load_state_from_file(self, file):
        # Initialize the data structures
        self._init_ical()

        # Read the data and figure out the encoding
        data = file.read()
        encoding = Text.guess_encoding(data)
        self.encoding = encoding

        # Parse
        lines = []
        for name, value, parameters in parse_table(data):
            # Deserialize
            datatype = self.get_datatype(name)
            if isinstance(datatype, Unicode):
                value = datatype.decode(value, encoding=encoding)
            else:
                value = datatype.decode(value)
            # Build the value (a PropertyValue instance)
            value = PropertyValue(value, **parameters)
            # Append
            lines.append((name, value))

        # Read first line
        first = lines[0]
        if (first[0] != 'BEGIN' or first[1].value != 'VCALENDAR'
            or len(first[1].parameters) != 0):
            raise ValueError, 'icalendar must begin with BEGIN:VCALENDAR'

        lines = lines[1:]

        ###################################################################
        # Read properties
        n_line = 0
        for name, value in lines:
            if name == 'BEGIN':
                break
            elif name == 'END':
                break
            elif name == 'VERSION':
                if 'VERSION' in self.properties:
                    raise ValueError, 'VERSION can appear only one time'
            elif name == 'PRODID':
                if 'PRODID' in self.properties:
                    raise ValueError, 'PRODID can appear only one time'
            # Add the property
            self.properties[name] = value
            n_line += 1

        # The properties VERSION and PRODID are mandatory
        if 'VERSION' not in self.properties or 'PRODID' not in self.properties:
            raise ValueError, 'PRODID or VERSION parameter missing'

        lines = lines[n_line:]

        ###################################################################
        # Read components
        c_type = None
        uid = None

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

                    if uid in self.components:
                        component = self.components[uid]
                        component.add_version(c_properties)
                    else:
                        component = Component(c_type, uid)
                        component.add_version(c_properties)
                        self.components[uid] = component
                    # Next
                    c_type = None
                    uid = None
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
                    if datatype.occurs == 1:
                        # Check the property has not yet being found
                        if prop_name in c_properties:
                            msg = ('the property %s can be assigned only one'
                                   ' value' % prop_name)
                            raise ValueError, msg
                        # Set the property
                        c_properties[prop_name] = prop_value
                    else:
                        value = c_properties.setdefault(prop_name, [])
                        value.append(prop_value)

        ###################################################################
        # Index components
        for uid in self.components:
            component = self.components[uid]
            self.catalog.index_document(component, uid)


    #########################################################################
    # Save State
    #########################################################################
    @classmethod
    def encode_property(cls, name, property_values, encoding='utf-8'):
        if not isinstance(property_values, list):
            property_values = [property_values]

        datatype = cls.get_datatype(name)

        lines = []
        for property_value in property_values:
            # The parameters
            parameters = ''
            for param_name in property_value.parameters:
                param_value = property_value.parameters[param_name]
                parameters += ';%s=%s' % (param_name, ','.join(param_value))

            # The value (encode)
            value = property_value.value
            if isinstance(datatype, Unicode):
                value = datatype.encode(value, encoding=encoding)
            else:
                value = datatype.encode(value)
            # The value (escape)
            value = escape_data(value)

            # Build the line
            line = '%s%s:%s\n' % (name, parameters, value)

            # Append
            lines.append(fold_line(line))

        return lines


    def to_str(self, encoding='UTF-8'):
        lines = []

        line = 'BEGIN:VCALENDAR\n'
        lines.append(Unicode.encode(line))

        # Calendar properties
        for key in self.properties:
            value = self.properties[key]
            line = self.encode_property(key, value, encoding)
            lines.extend(line)
        # Calendar components
        for uid in self.components:
            component = self.components[uid]
            c_type = component.c_type
            for sequence in component.get_sequences():
                version = component.versions[sequence]
                # Begin
                line = 'BEGIN:%s\n' % c_type
                lines.append(Unicode.encode(line))
                # UID, SEQUENCE
                lines.append('UID:%s\n' % uid)
                lines.append('SEQUENCE:%s\n' % sequence)
                # Properties
                for key in version:
                    value = version[key]
                    line = self.encode_property(key, value, encoding)
                    lines.extend(line)
                # End
                line = 'END:%s\n' % c_type
                lines.append(Unicode.encode(line))

        line = 'END:VCALENDAR\n'
        lines.append(Unicode.encode(line))

        return ''.join(lines)


    def to_text(self):
        text = []
        for uid in self.components:
            version = self.components[uid].get_version()
            for key in ['SUMMARY', 'DESCRIPTION']:
                if key in version:
                    text.append(version[key].value)
        return ' '.join(text)


    #######################################################################
    # To override
    #######################################################################
    @classmethod
    def generate_uid(cls, c_type='UNKNOWN'):
        """ Generate a uid based on c_type and current datetime. """
        return ' '.join([c_type, datetime.now().isoformat()])


    #######################################################################
    # API
    #######################################################################
    def check_properties(self, properties):
        """
        Check each property has a correct number of occurrences.
        It replaces a unique value of a multiple occurrences allowed
        property by a list with this value.
        """
        for name, value in properties.items():
            datatype = self.get_datatype(name)
            if datatype.occurs == 1:
                if isinstance(value, list):
                    msg = 'property "%s" requires only one value' % name
                    raise TypeError, msg
            else:
                if not isinstance(value, list):
                    properties[name] = [value]

        return properties


    def add_component(self, c_type, **kw):
        """
        Add a new component of type c_type.
        It generates a uid and a new version with the given properties if any.
        """
        # Check the properties
        kw = self.check_properties(kw)

        # Build the component
        uid = self.generate_uid(c_type)
        component = Component(c_type, uid)

        # Add the component
        self.set_changed()
        self.components[uid] = component
        # Remove SEQUENCE number if any
        if 'SEQUENCE' in kw:
            del kw['SEQUENCE']
        component.add_version(kw)

        # Index the component
        self.catalog.index_document(component, uid)

        return uid


    def update_component(self, uid, **kw):
        """
        Update component with given uid with properties given as kw,
        creating a new version based on the previous one.
        """
        # Check the properties
        kw = self.check_properties(kw)

        # Build the new version
        component = self.components[uid]
        version = component.get_version()
        version = version.copy()
        # Remove SEQUENCE number if any
        if 'SEQUENCE' in kw:
            del kw['SEQUENCE']
        version.update(kw)
        # Remove deleted properties (value is None or [None])
        keys = []
        for key in version:
            if version[key] is None or version[key] == [None]:
                keys.append(key)
        for key in keys:
            del version[key]

        self.set_changed()
        # Unindex the component, add new version, index again
        self.catalog.unindex_document(component, uid)
        component.add_version(version)
        self.catalog.index_document(component, uid)


    def remove(self, uid):
        """
        Definitely remove from the calendar an existant component with all its
        versions.
        """
        self.set_changed()
        # Remove
        component = self.components[uid]
        del self.components[uid]
        # Unindex
        self.catalog.unindex_document(component, uid)


    def get_property_values(self, name=None):
        """
        Return PropertyValue[] for the given icalendar property name
        or
        Return icalendar property values as a dict
            {property_name: PropertyValue object, ...}

        *searching only for general properties, not components ones.
        """
        if name:
            return self.properties.get(name, None)
        return self.properties


    def set_property(self, name, values):
        """
        Set values to the given calendar property, removing previous ones.

        name -- name of the property as a string
        values -- PropertyValue[]
        """
        datatype = self.get_datatype(name)
        if datatype.occurs == 1:
            # If the property can occur only once, set the first value of the
            # list, ignoring others
            if isinstance(values, list):
                values = values[0]
        else:
            # Get a list if it is not.
            if not isinstance(values, list):
                values = [values]

        self.set_changed()
        self.properties[name] = values


    def get_components(self, type=None):
        """
        Return a dict {component_type: Component[], ...}
        or
        Return Component[] of given type.
        """
        if type is None:
            return self.components

        return [ self.components[x] for x in self.search(type=type) ]


    # Get some events corresponding to arguments
    def search_events(self, subset=None, **kw):
        """
        Return a list of Component objects of type 'VEVENT' corresponding to
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
        events = subset or [self.components[x]
                            for x in self.search(type='VEVENT')]
        for event in events:
            version = event.get_version()

            # For each filter
            for filter in filters:
                # If filter not in component, go to next one
                if filter not in version:
                    break
                # Test filter
                expected = kw.get(filter)
                property_value = version[filter]
                datatype = self.get_datatype(filter)
                if datatype.occurs == 1:
                    if property_value.value != expected:
                        break
                else:
                    for item in property_value:
                        if isinstance(expected, list):
                            if item.value in expected:
                                break
                        elif item.value == expected:
                            break
                    else:
                        break
            else:
                res_events.append(event)
        return res_events


    # Used to factorize code of cms ical between Calendar & CalendarTable
    def get_record(self, uid):
        return self.components.get(uid)


    def get_component_by_uid(self, uid):
        """
        Return components with the given uid, None if it doesn't appear.
        """
        return self.components.get(uid)


    def search_events_in_date(self, selected_date, sortby=None, **kw):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        date and sorted if requested.
        """
        dtstart = datetime(selected_date.year, selected_date.month,
                           selected_date.day)
        dtend = dtstart + timedelta(days=1) - resolution
        return self.search_events_in_range(dtstart, dtend, sortby=sortby, **kw)


    def search_events_in_range(self, dtstart, dtend, sortby=None, **kw):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        dates range and sorted  if requested.
        If kw is filled, it calls search_events on the found subset to return
        only components matching filters.

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
            OrQuery(RangeQuery('dtstart', dtstart, dtend),
                    RangeQuery('dtend', dtstart_limit, dtend_limit),
                    AndQuery(RangeQuery('dtstart', None, dtstart),
                             RangeQuery('dtend', dtend, None))))
        results = [self.components[uid] for uid in self.search(query)]

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
            version = event.get_version()
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


    # Test if any event corresponds to a given date
    def has_event_in_date(self, date):
        """
        Return True if there is at least one event matching the given date.
        """
        return self.search_events_in_date(date) != []


    def get_conflicts(self, date):
        """
        Returns a list of uid couples which happen at the same time.
        We check only last occurrence of events.
        """
        events = self.search_events_in_date(date)
        if len(events) <= 1:
            return None

        conflicts = []
        # We take each event as a reference
        for i, event_ref in enumerate(events):
            version = event_ref.get_version()
            dtstart_ref = version['DTSTART'].value
            dtend_ref = version['DTEND'].value
            # For each other event, we test if there is a conflict
            for j, event in enumerate(events):
                if j <= i:
                    continue
                version = event.get_version()
                dtstart = version['DTSTART'].value
                dtend = version['DTEND'].value

                if dtstart >=  dtend_ref or dtend <= dtstart_ref:
                    continue
                conflicts.append((i, j))

        # Replace index of components by their UID
        if conflicts != []:
            for index, (i, j) in enumerate(conflicts):
                conflicts[index] = (events[i].uid, events[j].uid)

        return conflicts


    #######################################################################
    # API / Search
    def get_analyser(self, name):
        try:
            return self.catalog.analysers[name]
        except KeyError:
            raise ValueError, 'the field "%s" is not indexed' % name


    def get_index(self, name):
        try:
            return self.catalog.indexes[name]
        except KeyError:
            raise ValueError, 'the field "%s" is not indexed' % name


    def search(self, query=None, **kw):
        """
        Return list of component internal ids returned by executing the query.
        """
        if query is None:
            if kw:
                atoms = []
                for key, value in kw.items():
                    atoms.append(PhraseQuery(key, value))

                query = AndQuery(*atoms)
            else:
                raise ValueError, "expected a query"

        documents = query.search(self)
        uids = documents.keys()
        # Sort by weight
        uids.sort()

        return uids



class Record(TableRecord):
    """
    A Record with some icalendar specific methods in addition.
    """

    def get_version(self, sequence=None):
        """
        Return the last version of current component or the sequence's one.
        """
        if sequence is None:
            sequence = self[-1]
        for version in self:
            if self.get_property('SEQUENCE') == sequence:
                return version
        return None


    # Get a property of current component
    def get_property(self, name=None):
        """
        Return the value of given name property as a Property or as a list
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
        """
        Specify the namespace given on views to represent an event.

        day: date selected XXX not used for now
        conflicts_list: list of conflicts for current resource, [] if not used
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



class icalendarTable(Table):
    """
    An icalendarTable is a handler for calendar data, generally used as an ical
    file but here as a table object.
    """

    schema = {
      'type': String(index='keyword'),
      # Calendar properties
      'BEGIN': String,
      'END': String,
      'VERSION': Unicode,
      'PRODID': Unicode,
      'METHOD': Unicode,
      # Component properties
      'ATTACH': URI(multiple=True),
      'CATEGORY': Unicode,
      'CATEGORIES': Unicode(multiple=True),
      'CLASS': Unicode,
      'COMMENT': Unicode(multiple=True),
      'DESCRIPTION': Unicode,
      'GEO': Unicode,
      'LOCATION': Unicode,
      'PERCENT-COMPLETE': Integer,
      'PRIORITY': Integer,
      'RESOURCES': Unicode(multiple=True),
      'STATUS': Unicode,
      'SUMMARY': Unicode(index='text', mandatory=True),
      # Date & Time component properties
      'COMPLETED': DateTime,
      'DTEND': DateTime(index='keyword'),
      'DUE': DateTime,
      'DTSTART': DateTime(index='keyword'),
      'DURATION': Unicode,
      'FREEBUSY': Unicode,
      'TRANSP': Unicode,
      # Time Zone component properties
      'TZID': Unicode,
      'TZNAME': Unicode(multiple=True),
      'TZOFFSETFROM': Unicode,
      'TZOFFSETTO': Unicode,
      'TZURL': URI,
      # Relationship component properties
      'ATTENDEE': URI(multiple=True),
      'CONTACT': Unicode(multiple=True),
      'ORGANIZER': URI,
      # Recurrence component properties
      'EXDATE': DateTime(multiple=True),
      'EXRULE': Unicode(multiple=True),
      'RDATE': Unicode(multiple=True),
      'RRULE': Unicode(multiple=True),
      # Alarm component properties
      'ACTION': Unicode,
      'REPEAT': Integer,
      'TRIGGER': Unicode,
      # Change management component properties
      'CREATED': DateTime,
      'DTSTAMP': DateTime,
      'LAST-MODIFIED': DateTime,
      'SEQUENCE': Integer,
      # Others
      'RECURRENCE-ID': DateTime,
      'RELATED-TO': Unicode,
      'URL': URI,
      'UID': String(index='keyword')
    }


    def new(self):
        Table.new(self)

        properties = (
            ('VERSION', {}, u'2.0'),
            ('PRODID', {}, u'-//itaapy.com/NONSGML ikaaro icalendar V1.0//EN')
          )
        self.properties = {}
        for name, param, value in properties:
            self.properties[name] = Property(value, param)


    #########################################################################
    # Load State
    #########################################################################
    def _load_state_from_ical_file(self, file):
        """
        Deserialize an ical file, generally named .ics
        Output data structure is a table.
        """
        self.new()

        properties = {}
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
        # Read properties
        n_line = 0
        for name, value in lines:
            if name == 'BEGIN':
                break
            elif name == 'END':
                break
            elif name == 'VERSION':
                if 'VERSION' in properties:
                    raise ValueError, 'VERSION can appear only one time'
            elif name == 'PRODID':
                if 'PRODID' in properties:
                    raise ValueError, 'PRODID can appear only one time'
            # Add the property
            properties[name] = value
            n_line += 1

        # The properties VERSION and PRODID are mandatory
        if 'VERSION' not in properties or 'PRODID' not in properties:
            raise ValueError, 'PRODID or VERSION parameter missing'

        # Save calendar properties
        self.properties = properties

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
        """ Serialize as an ical file, generally named .ics """
        lines = []

        line = 'BEGIN:VCALENDAR\n'
        lines.append(Unicode.encode(line))

        # Calendar properties
        for name in self.properties:
            value = self.properties[name]
            line = icalendar.encode_property(name, value)
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
                        line = icalendar.encode_property(name, value)
                        lines.extend(line)
                    line = 'END:%s\n' % c_type
                    lines.append(Unicode.encode(line))
                    seq += 1

        line = 'END:VCALENDAR\n'
        lines.append(Unicode.encode(line))

        return ''.join(lines)


    def set_property(self, name, values):
        """
        Set values to the given calendar property, removing previous ones.

        name -- name of the property as a string
        values -- Property[]
        """
        self.properties[name] = values
        self.set_changed()


    def add_record(self, kw):
        if 'UID' not in kw:
            uid = icalendar.generate_uid(kw.get('type', 'UNKNOWN'))
            kw['UID'] = uid

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
        """
        Return components with the given uid, None if it doesn't appear.
        """
        return self.search(UID=uid)


    def get_property(self, name=None):
        """
        Return Property[] for the given icalendar property name
        or
        Return icalendar property values as a dict
            {property_name: Property object, ...}

        *searching only for general properties, not components ones.
        """
        if name:
            return self.properties.get(name, None)
        return self.properties


    # Deprecated
    def get_components(self, type=None):
        """
        Return a dict {component_type: Record[], ...}
        or
        Return Record[] of given type.
        """
        if type is None:
            return self.records

        return self.search(type=type)


    # Get some events corresponding to arguments
    def search_events(self, subset=None, **kw):
        """
        Return a list of Record objects of type 'VEVENT' corresponding to
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
        """
        Return a list of Records objects of type 'VEVENT' matching the given
        dates range and sorted if requested.
        If kw is filled, it calls search_events on the found subset to return
        only components matching filters.

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
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        date and sorted if requested.
        """
        dtstart = datetime(selected_date.year, selected_date.month,
                           selected_date.day)
        dtend = dtstart + timedelta(days=1) - resolution
        return self.search_events_in_range(dtstart, dtend, sortby=sortby, **kw)


    # Test if any event corresponds to a given date
    def has_event_in_date(self, date):
        """
        Return True if there is at least one event matching the given date.
        """
        return self.search_events_in_date(date) != []


    def get_conflicts(self, date):
        """
        Returns a list of uid couples which happen at the same time.
        We check only last occurrence of events.
        """
        events = self.search_events_in_date(date)
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

