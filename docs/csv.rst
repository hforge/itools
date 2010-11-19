:mod:`itools.csv` -- CSV files support
**************************************

.. module:: itools.csv
   :synopsis: a Comma Separated Values files support

.. index::
   single: CSV files

.. contents::


This chapter is dedicated to the :mod:`itools.csv` package, which offers a
handler (cf :mod:`itools.handlers`) to work with CSV files.

This handler is interesting to use when the CSV file at hand has the structure
it is expected to have. That is to say, when it represents a table where each
row has the same number of columns, and where each column contains a value of
the expected type. For instance:

  ========= ================ ================= =================
  Client Id Name             E-Mail            Registration Date
  ========= ================ ================= =================
  1         Piotr Macuk      piotr@macuk.pl    2004-11-09
  --------- ---------------- ----------------- -----------------
  2         \J. David Ibañez jdavid@itaapy.com 2006-01-01
  ========= ================ ================= =================

The functional scope of the CSV handler, what it is able to do, is:

* Offers a programming interface to get, add and remove rows.
* If an schema is defined, the values will be deserialized, so we will work
  with text strings, integers and booleans (instead of byte strings).


Introduction to the programming interface
=========================================

Let's assume we have a :file:`clients.csv` file, we will load it as we do with
any other handler::

    >>> import itools.csv
    >>> from itools.handlers import RWDatabase
    >>>
    >>> rw_database = RWDatabase()
    >>> clients = rw_database.get_handler('clients.csv')

And we can work with it straight away::

    >>> row = clients.get_row(0)
    >>> row
    ['1', 'Piotr Macuk', 'piotr@macuk.pl', '2004-11-09']
    >>> print type(row)
    <class 'itools.csv.csv_.Row'>
    >>> print row.get_value(1)
    Piotr Macuk

The method :meth:`get_row` returns the row at the given row number. The value
returned appears as a list of byte strings, but it is actually an instance of
the class :class:`Row`. This class offers a programming interface to get the
value from a given column (where the column is identified by its position: 0,
1, 2, etc.).

To modify a row we use the :meth:`update_row` method from the CSV file::

    >>> print row.get_value(3)
    2004-11-09
    >>> clients.update_row(0, **{'3': '2004-11-10'})
    >>> print row.get_value(3)
    2004-11-10

The method :meth:`update_row` allows to modify several columns of the row at
once with keyword parameters.  Since the field is identified by a number (the
column number) the call to :meth:`update_row` is quite ugly (things get better
when we work with schemas, see :ref:`csv-schema`).

Note: remember that as with any other handler, the changes made to the CSV
handler are done in memory, and not saved until explicitly said so with
:meth:`save_state`. Check :mod:`itools.handlers` for the details.

Here we describe with examples the other basic methods offered by CSV
handlers::

    >>>
    # Return the number of rows
    >>> print clients.get_nrows()
    250
    # Return all rows (a generator)
    >>> for row in clients.get_rows():
    ...     print row
    ...
    # Return the rows at the given positions
    >>> for row in clients.get_rows([2,3,7,52]):
    ...     print row
    ...
    # Add a new row (the input parameter is a list)
    >>> clients.add_row(
    ...     ['250', 'J. David Ibanez', 'jdavid@itaapy.com',
    ...      '2007-01-01'])
    ...
    # Remove a row
    >>> clients.del_row(5)
    # Remove many rows
    >>> clients.del_rows([5, 6, 19])


.. _csv-schema:

The schema
==========

If we define a schema we will be able to load not byte strings, but values
with a type (integers, booleans, etc.). We do so by sub-classing::

    from itools.datatypes import Integer, Unicode, String, Date
    from itools.csv import CSVFile

    class Clients(CSVFile):

        columns = ['client_id', 'name', 'email',
            'registration_date']

        schema = {
            'client_id': Integer,
            'name': Unicode,
            'email': String,
            'registration_date': Date}

Now, if we load the CSV file with our new shinny class, we will be able
to get values with a type, and to do other nice things::

    >>> clients = rw_database.get_handler('clients.csv', Clients)
    >>>
    >>> row = clients.get_row(0)
    >>> row
    [1, u'Piotr Macuk', 'piotr@macuk.pl',
     datetime.date(2004, 11, 09)]
    # Access a column by its name
    >>> print row.get_value('name')
    Piotr Macuk
    # Now 'update_row' expects the values to be of the good type
    >>> from datetime import date
    >>>
    >>> clients.update_row(0, registration_date=date(2004, 11, 10))
    # So is for the 'add_row' method
    >>> clients.add_row(
    ...     [250, u'J. David Ibanez', 'jdavid@itaapy.com',
    ...      date(2007, 1, 1)])

As we have seen the schema is defined with the class variable :attr:`columns`,
which gives a name to each column, and with the class variable :attr:`schema`,
which defines the type.

