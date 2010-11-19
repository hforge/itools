:mod:`itools.ical` -- iCalendar
*******************************

.. module:: itools.ical
   :synopsis: iCalendar

.. index::
   single: iCalendar

.. contents::


In this chapter you will learn how to work with calendaring and scheduling
resources by using the :mod:`itools.ical` API. This module is based on using
standard type ical specified in the RFC 2445 [#ical-rfc2445]_.


What is an ical file?
=====================

An ical file follow a strict organization. It is composed by a main element
called icalendar object. This element contains a few properties and components.
These components contain themselves several properties and sometimes inner
components. The properties are composed by a name, a value, and some optional
parameters. Below is a simple example:

.. code-block:: none

    BEGIN:VCALENDAR
    VERSION:2.0
    PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN
    METHOD:PUBLISH
    BEGIN:VEVENT
    UID:581361a0-1dd2-11b2-9a42-bd3958eeac9a
    SUMMARY: title
    DESCRIPTION : description of the event
    DTSTART:20050530
    DTEND:20050531
    ATTENDEE
     ;RSVP=TRUE
     ;MEMBER="MAILTO:DEV-GROUP@host2.com"
     :MAILTO:jdoe@itaapy.com
    END:VEVENT
    END:VCALENDAR


Simple use of the API
=====================

We will illustrate how to create an icalendar object, and manipulate it.


Create an icalendar object
--------------------------

First, we create an icalendar object with the needed properties (Version and
Prodid) but without any component::

    >>> from itools.ical import iCalendar
    >>> cal = iCalendar()
    >>> from pprint import pprint
    >>> pprint(cal.get_property_values())
    {'PRODID': <itools.csv.table.Property object at 0xa76cce8c>,
     'VERSION': <itools.csv.table.Property object at 0xa76cceec>}

You can see that the two needed properties have been automatically added.


Add a property to an icalendar object
-------------------------------------

We can add an other property to this icalendar object::

    >>> from itools.csv import Property
    >>> cal.properties['METHOD'] = Property('PUBLISH')


Add a component to an icalendar object
--------------------------------------

We create a component of type 'VEVENT' with some properties and add it to the
icalendar object::

    >>> from datetime import datetime
    >>> properties = {}
    >>> properties['SUMMARY'] = Property('Europython 2006')
    >>> properties['DTSTART'] = Property(datetime(2006, 07, 03))
    >>> properties['DTEND'] = Property(datetime(2006, 07, 05))
    >>> uid = cal.add_component('VEVENT', **properties)

Now we add some new properties to this event, accessing it by its uid.


Add properties to a component
-----------------------------
::

    >>> properties = {'LOCATION': Property('Cern (Switzerland)')}
    >>> cal.update_component(uid, **properties)

We can also add a more precised property which contains a parameter.


Add a property with parameter
-----------------------------
::

    >>> parameters = {'MEMBER': ['MAILTO:DEV-GROUP@host.com']}
    >>> value = Property('mailto:darwin@itaapy.com', **parameters)
    >>> cal.update_component(uid, ATTENDEE=value)
    >>>
    >>> event = cal.get_component_by_uid(uid)
    >>> pprint(event.get_property())
    {'ATTENDEE': [<itools.csv.table.Property object at 0xa7727e2c>],
     'DTEND': <itools.csv.table.Property object at 0xa7ad394c>,
     'DTSTAMP': <itools.csv.table.Property object at 0xb779a86c>,
     'DTSTART': <itools.csv.table.Property object at 0xa7727b2c>,
     'LOCATION': <itools.csv.table.Property object at 0xa7727dac>,
     'SUMMARY': <itools.csv.table.Property object at 0xa7727d8c>}

You can see that all properties have a PropertyValue except the ``ATTENDEE``
property which has a PropertyValue list, because this property can occur more
than once inside of a component.


Manipulate properties
---------------------

You can get the value(s) of a property by its name::

    >>> summary = event.get_property_values('SUMMARY')
    >>> print summary.value, summary.parameters
    Europython 2006 {}
    >>>
    >>> attendees = event.get_property_values('ATTENDEE')
    >>> print attendees
    [<itools.csv.table.Property object at 0xa7727e2c>]
    >>> print attendees[0].value
    mailto:darwin@itaapy.com
    >>> print attendees[0].parameters
    {'MEMBER': ['MAILTO:DEV-GROUP@host.com']}
    >>>


.. rubric:: Footnotes

.. [#ical-rfc2445] http://www.faqs.org/rfcs/rfc2445.html
