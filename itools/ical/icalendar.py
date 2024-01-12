# Copyright (C) 2005 Nicolas Oyez <nicoyez@gmail.com>
# Copyright (C) 2005-2007, 2009 Nicolas Deram <nderam@gmail.com>
# Copyright (C) 2005-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006-2008 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2008-2010 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2010 Alexis Huet <alexis@itaapy.com>
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
from datetime import date, datetime, timedelta, tzinfo

# Import from itools
from itools.core import freeze
from itools.csv import Property, parse_table, deserialize_parameters
from itools.csv import property_to_str
from itools.datatypes import String, Unicode
from itools.handlers import guess_encoding, TextFile
from .datatypes import DateTime, record_properties, record_parameters, Time


class Component:
    """Parses and evaluates a component block.

        input :   string values for c_type and uid
                  a list of Property objects
                  (Property objects can share the same name as a property
                  name can appear more than one time in a component)

        output :  unchanged c_type and uid
                  a dictionnary of versions of this component including
                  a dict {'property_name': Property[] } for properties
    """
    # XXX A parse method should be added to test properties inside of current
    # component-type/properties (for example to test if property can appear
    # more than one time, ...)

    def __init__(self, c_type, uid):
        """Initialize the component.

        c_type -- type of component as a string (i.e. 'VEVENT')
        uid -- uid of a VEVENT, tzid of a VTIMEZONE
        """
        self.c_type = c_type
        self.uid = uid
        self.versions = {}

    #######################################################################
    # API / Private
    #######################################################################
    def get_sequences(self):
        sequences = self.versions.keys()
        return sorted(list(sequences))

    def add_version(self, properties):
        # Sequence in properties only if just loading file
        if 'SEQUENCE' in properties:
            sequence = properties.pop('SEQUENCE')
            sequence = sequence.value
        else:
            sequences = self.get_sequences()
            if sequences:
                sequence = list(sequences)[-1] + 1
            else:
                sequence = 0

        # Timestamp
        if 'DTSTAMP' not in properties:
            properties['DTSTAMP'] = Property(datetime.today())

        self.versions[sequence] = properties

    #######################################################################
    # API / Public
    #######################################################################
    def get_version(self, sequence=None):
        """Return the last version of current component or the sequence's one.
        """
        if sequence is None:
            sequence = list(self.get_sequences())[-1]
        return self.versions[sequence]


    def get_property(self, name=None):
        """Return the value of given name property as a Property or as a
        list of Property objects if it can occur more than once.

        Return icalendar property values as a dict {name: value, ...} where
        value is a Property or a list of Property objects if it can
        occur more than once.

        Note that it return values for the last version of this component.
        """
        version = self.get_version()
        if name:
            return version.get(name, None)
        return version

    get_property_values = get_property

    # TODO Move this: with Components that are not VEVENT, it will fail
    def get_ns_event(self, day, resource_name=None, conflicts_list=freeze([]),
                     timetable=None, grid=False, starts_on=True, ends_on=True,
                     out_on=True):
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

          XXX url: url to access edit_event_form on current event
        """
        get_property = self.get_property
        ns = {}
        ns['SUMMARY'] = get_property('SUMMARY').value
        ns['ORGANIZER'] = get_property('ORGANIZER').value

        ###############################################################
        # Set dtstart and dtend values using '...' for events which
        # appear into more than one cell
        start = get_property('DTSTART')
        end = get_property('DTEND')
        start_value_type = start.get_parameter('VALUE', 'DATE-TIME')

        ns['start'] = Time.encode(start.value.time())
        ns['end'] = Time.encode(end.value.time())
        ns['TIME'] = None
        if grid:
            # Neither a full day event nor a multiple days event
            if (start_value_type != 'DATE'
                and start.value.date() == end.value.date()):
                ns['TIME'] = f"{ns['start']} - {ns['end']}"
            else:
                ns['start'] = ns['end'] = None
        elif not out_on:
            if start_value_type != 'DATE':
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
            ns['STATUS'] = 'cal_busy'
            status = get_property('STATUS')
            if status:
                ns['STATUS'] = status.value

        if not resource_name:
            id = str(id)
        else:
            id = f'{resource_name}/{id}'
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


class iCalendar(TextFile):
    """icalendar structure :

        BEGIN:VCALENDAR

            --properties
                     required : PRODID, VERSION
                     optionnal : CALSCALE, METHOD, non-standard ones...

            --components(min:1)
                     VEVENT, TODO, JOURNAL, FREEBUSY, TIMEZONE,
                     iana component, non-standard component...

        END:VCALENDAR
    """

    class_mimetypes = ['text/calendar']
    class_extension = 'ics'

    record_properties = record_properties
    record_parameters = record_parameters


    @classmethod
    def get_record_datatype(cls, name):
        if name in cls.record_properties:
            return cls.record_properties[name]
        # Default
        return String(multiple=True)

    def generate_uid(self, c_type='UNKNOWN'):
        """Generate a uid based on c_type and current datetime.
        """
        return ' '.join([c_type, datetime.now().isoformat()])

    def encode_property(self, name, property_values, encoding='utf-8'):
        if type(property_values) is not list:
            property_values = [property_values]

        datatype = self.get_record_datatype(name)
        return [
            property_to_str(name, x, datatype, {}, encoding)
            for x in property_values]

    #########################################################################
    # New
    #########################################################################
    def reset(self):
        self.properties = {}
        self.timezones = {}
        self.components = {}

    def new(self):
        properties = (
            ('VERSION', '2.0'),
            ('PRODID', '-//hforge.org/NONSGML ikaaro icalendar V1.0//EN'))
        for name, value in properties:
            self.properties[name] = Property(value)

        # The encoding
        self.encoding = 'UTF-8'

    #########################################################################
    # Load State
    #########################################################################
    def _load_state_from_file(self, file):
        # Read the data and figure out the encoding
        data = file.read()
        encoding = guess_encoding(data)
        self.encoding = encoding

        # Parse
        lines = []
        for name, value, parameters in parse_table(data):
            # Deserialize
            datatype = self.get_record_datatype(name)
            if isinstance(datatype, Unicode):
                value = datatype.decode(value, encoding=encoding)
            else:
                value = datatype.decode(value)
            # Build the value (a Property instance)
            deserialize_parameters(parameters, self.record_parameters)
            value = Property(value, **parameters)
            # Append
            lines.append((name, value))

        # Read first line
        first = lines[0]
        if (first[0] != 'BEGIN' or first[1].value != 'VCALENDAR'
            or first[1].parameters):
            raise ValueError('icalendar must begin with BEGIN:VCALENDAR')

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
                    raise ValueError('VERSION can appear only one time')
            elif name == 'PRODID':
                if 'PRODID' in self.properties:
                    raise ValueError('PRODID can appear only one time')
            # Add the property
            self.properties[name] = value
            n_line += 1

        # The properties VERSION and PRODID are mandatory
        if ('VERSION' not in self.properties or
            'PRODID' not in self.properties):
            raise ValueError('PRODID or VERSION parameter missing')

        lines = lines[n_line:]

        ###################################################################
        # Read components
        c_type = None
        c_inner_type = None
        uid = None

        for prop_name, prop_value in lines[:-1]:
            if prop_name in ('PRODID', 'VERSION'):
                raise ValueError('PRODID and VERSION must appear before ' \
                                 'any component')
            if prop_name == 'BEGIN':
                if c_type is None:
                    c_type = prop_value.value
                    c_properties = {}
                    c_inner_components = []
                else:
                    # Inner component like DAYLIGHT or STANDARD
                    c_inner_type = prop_value.value
                    c_inner_properties = {}
            elif prop_name == 'END':
                value = prop_value.value
                if value == c_type:
                    if uid is None:
                        raise ValueError('UID is not present')

                    if c_type == 'VTIMEZONE':
                        timezone = VTimezone(uid, c_inner_components)
                        timezone.content = c_properties
                        self.timezones[uid] = timezone
                    elif uid in self.components:
                        component = self.components[uid]
                        component.add_version(c_properties)
                    else:
                        component = Component(c_type, uid)
                        component.add_version(c_properties)
                        self.components[uid] = component
                    # Next
                    c_type = None
                    uid = None
                # Inner component
                elif value == c_inner_type:
                    inner_component = TZProp(c_inner_type, c_inner_properties)
                    c_inner_components.append(inner_component)
                    c_inner_type = None
                else:
                    raise ValueError('Component %s found, %s expected' \
                                     % (value, c_inner_type))
            else:
                datatype = self.get_record_datatype(prop_name)
                if c_inner_type is None:
                    if prop_name in ('UID', 'TZID'):
                        uid = prop_value.value
                    else:
                        if getattr(datatype, 'multiple', False) is True:
                            value = c_properties.setdefault(prop_name, [])
                            value.append(prop_value)
                        else:
                            # Check the property has not yet being found
                            if prop_name in c_properties:
                                msg = ('the property %s can be assigned only '
                                       'one value' % prop_name)
                                raise ValueError(msg)
                            # Set the property
                            c_properties[prop_name] = prop_value
                else:
                    # Inner component properties
                    if getattr(datatype, 'multiple', False) is True:
                        value = c_inner_properties.setdefault(prop_name, [])
                        value.append(prop_value)
                    else:
                        # Check the property has not yet being found
                        if prop_name in c_inner_properties:
                            msg = ('the property %s can be assigned only one'
                                   ' value' % prop_name)
                            raise ValueError(msg)
                        value = prop_value
                    # Set the property
                    c_inner_properties[prop_name] = value

    #########################################################################
    # Save State
    #########################################################################
    def to_str(self, encoding='UTF-8'):
        lines = ['BEGIN:VCALENDAR\n']

        # 1. Calendar properties
        for key, value in self.properties.items():
            line = self.encode_property(key, value, encoding)
            lines.extend(line)

        # 2. Timezones
        for tzid in self.timezones:
            timezone = self.timezones[tzid]
            # Begin
            lines.append('BEGIN:VTIMEZONE\n')
            # Properties
            lines.append(f'TZID:{tzid}\n')
            for key, value in timezone.content.items():
                line = self.encode_property(key, value, encoding)
                lines.extend(line)
            # Insert inner components
            for c_inner_component in timezone.tz_props:
                c_inner_type = c_inner_component.type
                # sequence not supported into inner components
                version = c_inner_component.properties
                # Begin
                lines.append(f'BEGIN:{c_inner_type}\n')
                # Properties
                for key, value in version.items():
                    line = self.encode_property(key, value, encoding)
                    lines.extend(line)
                # End
                lines.append(f'END:{c_inner_type}\n')
            # End
            lines.append('END:VTIMEZONE\n')

        # 3. Components
        for uid in self.components:
            component = self.components[uid]
            c_type = component.c_type
            for sequence in component.get_sequences():
                version = component.versions[sequence]
                # Begin
                lines.append(f'BEGIN:{c_type}\n')
                # Properties
                lines.append(f'UID:{uid}\n')
                lines.append(f'SEQUENCE:{sequence}\n')
                for key, value in version.items():
                    line = self.encode_property(key, value, encoding)
                    lines.extend(line)
                # End
                lines.append(f'END:{c_type}\n')

        # Ok
        lines.append('END:VCALENDAR\n')
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
    # API
    #######################################################################
    def check_properties(self, properties):
        """Check each property has a correct number of occurrences.  It
        replaces a unique value of a multiple occurrences allowed property by
        a list with this value.
        """
        for name, value in properties.items():
            datatype = self.get_record_datatype(name)
            if datatype.multiple is False:
                if isinstance(value, list):
                    msg = f'property "{name}" requires only one value'
                    raise TypeError(msg)
            else:
                if not isinstance(value, list):
                    properties[name] = [value]

        return properties

    def add_component(self, c_type, **kw):
        """Add a new component of type c_type.  It generates a uid and a new
        version with the given properties if any.
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

        return uid

    def update_component(self, uid, **kw):
        """Update component with given uid with properties given as kw,
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
        component.add_version(version)

    def remove(self, uid):
        """Definitely remove from the calendar an existant component with all
        its versions.
        """
        self.set_changed()
        del self.components[uid]

    def get_property_values(self, name=None):
        """Return Property[] for the given icalendar property name or
        Return icalendar property values as a dict
            {property_name: Property object, ...}

        searching only for general properties, not components ones.
        """
        if name:
            return self.properties.get(name, None)
        return self.properties

    def set_property(self, name, values):
        """Set values to the given calendar property, removing previous ones.

        name -- name of the property as a string
        values -- Property[]
        """
        datatype = self.get_record_datatype(name)
        if datatype.multiple is False:
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

    # Used to factorize code of cms ical between Calendar & CalendarTable
    def get_record(self, uid):
        return self.components.get(uid)

    def get_component_by_uid(self, uid):
        """Return components with the given uid, None if it doesn't appear.
        """
        return self.components.get(uid)

    def get_components(self, type=None):
        """Return the list of components of the given type, or all components
        if no type is given.
        """
        if type is None:
            return list(self.components.items()) + list(self.timezones.items())

        if type == 'VTIMEZONE':
            return [component for tzid, component in self.timezones.items()]
        return [component for uid, component in self.components.items()
                 if component.c_type == type]


class TZProp:
    """This class basically represent the concept of Timezone Property
    (standard or daylight), as described by RFC5545."""

    def __init__(self, type, properties):
        self.type = type
        self.properties = properties
        # Compute offset
        offset_to = self.properties['TZOFFSETTO'].value
        minutes = int(offset_to[3:5])
        hours = int(offset_to[1:3])
        sign = -1 if offset_to[0] == '-' else 1
        self.offset = sign * timedelta(hours=hours, minutes=minutes)
        # Compute second offset for DST
        offset_from = self.properties['TZOFFSETFROM'].value
        minutes = int(offset_from[3:5])
        hours = int(offset_from[1:3])
        sign = -1 if offset_from[0] == '-' else 1
        # DST if positive or null
        offset_from = sign * timedelta(hours=hours, minutes=minutes)
        self.dst = max(timedelta(0),
                       self.offset - offset_from)
        # Compute recurrency
        self.rec_dic = {}
        if 'RRULE' in self.properties:
            rrules = self.properties['RRULE']
            # FIXME RRULE can be multiple !
            rrule = rrules[0]
            for prop in rrule.value.split(';'):
                name, value = prop.split('=')
                self.rec_dic[name] = value

    def get_offset(self):
        return self.offset

    def get_date(self, dt):
        iso_weekdays = {'MO': 1, 'TU': 2, 'WE': 3, 'TH': 4,
            'FR': 5, 'SA': 6, 'SU': 7}
        # Default values
        year = dt.year
        day = 1
        month = 1
        delta = 0
        # Compute period for this year
        rec_dic = self.rec_dic
        freq = rec_dic['FREQ'] if 'FREQ' in rec_dic else None
        if freq == 'YEARLY':
            if 'BYMONTH' in self.rec_dic:
                month = int(self.rec_dic['BYMONTH'])
            if 'BYDAY' in self.rec_dic:
                byday = self.rec_dic['BYDAY']
                if byday[0] == '-':
                    sign = -1
                    month += 1
                else:
                    sign = 1
                if byday[0] in ('+', '-'):
                    byday = byday[1:]
                num = int(byday[:-2])
                byday = int(iso_weekdays[byday[-2:]])
                day = date(year, month, day)
                weekday = day.isoweekday()
                weeks_delta = (num - 1) * 7
                time = self.properties['DTSTART'].value.time()
                if sign == -1:
                    delta = (7 + weekday - byday) % 7 + weeks_delta
                    return datetime.combine(day, time) - timedelta(delta)
                else:
                    delta = (7 + byday - weekday) % 7 + weeks_delta
                    return datetime.combine(day, time) + timedelta(delta)
        elif 'RDATE' in self.properties:
            dates = [self.properties['DTSTART'].value]
            for rdate in self.properties['RDATE']:
                dates.append(DateTime.decode(rdate.value))
            for d in dates:
                if d.year == dt.year:
                    return d
            return None
        else:
            raise NotImplementedError('We only implement FREQ in  (YEARLY, )')

    def get_begin(self):
        return self.properties['DTSTART'].value

    def get_names(self):
        for name in self.properties['TZNAME']:
            yield (name.value, name.parameters)


class VTimezone(tzinfo):
    """This class represent a Timezone with TZProps builded from an ICS file"""

    content = None

    def __init__(self, tzid, tz_props):
        self.tzid = tzid
        if len(tz_props) < 1:
            raise ValueError('A VTIMEZONE MUST contain at least one TZPROP')
        self.tz_props = tz_props
        self.tz_props = sorted(tz_props, key=lambda x: x.get_begin())

    def get_tz_prop(self, dt):
        props = self.tz_props
        naive = dt.replace(tzinfo=None)
        candidates = []
        # Keep only tzprop corresponding to dt
        for i, prop in enumerate(props):
            begin = prop.get_begin()
            if begin > naive:
                continue
            for next in props[i:]:
                if next.type != prop.type:
                    next_prop = next
                    continue
            end = next_prop.get_begin() if next_prop else None
            if begin <= naive and ( end is None or naive < end):
                candidates.append(prop)

        if len(candidates) == 0:
            return None
        elif len(candidates) == 1:
            return candidates[0]
        # TZProp with same type mustn't overleap: it should remains one of each
        assert len(candidates) >= 2
        # Compute dston and dstend for dt.year
        c_dl = 0
        c_std = 0
        for tzprop in candidates:
            if tzprop.type == 'STANDARD':
                c_std += 1
                std, dstoff = tzprop, tzprop.get_date(dt)
            elif tzprop.type == 'DAYLIGHT':
                c_dl += 1
                dl, dston = tzprop, tzprop.get_date(dt)
            else:
                raise ValueError('TZProps are not consistent')
        if dston <= naive and naive < dstoff:
            return dl
        else:
           return std

    def tzname(self, dt):
        tz_prop = self.get_tz_prop(dt)
        # FIXME TZNAME property is multiple and can have language property
        value, parameters = next(tz_prop.get_names())
        return str(value)

    def utcoffset(self, dt):
        tz_prop = self.get_tz_prop(dt)
        return tz_prop.offset

    def dst(self, dt):
        if dt is None or dt.tzinfo is None:
            return timedelta(0)
        assert dt.tzinfo is self

        tz_prop = self.get_tz_prop(dt)
        return tz_prop.dst
