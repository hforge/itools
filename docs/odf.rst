:mod:`itools.odf` -- Open Document Format support
*************************************************

.. module:: itools.odf
   :synopsis: ODF support

.. index::
   single: Open Document Format (ODF)

.. contents::

The package :mod:`itools.odf` provides support for the Open Document Format
[#odf-specifications]_.


STL and Open Document Format
============================

You can use the STL and the ODF handler to produce documents. It's useful to
do mailings. The :func:`stl_to_odt` function allow to use substitution
placeholders (ex: ``${firstname}``) in an ODF file to compute substitutions.

Here a python example to generate a letter::

    #!/usr/bin/env python
    # -*- coding: UTF-8 -*-

    from itools.fs import lfs
    from itools.handlers import RWDatabase
    from itools.odf.odf import stl_to_odt, ODTFile

    namespace = {'firstname': 'Jean',
                 'lastname': 'Dupond'}
    # Load the model
    rw_database = RWDatabase(fs=lfs)
    handler = rw_database.get_handler('model_letter.odt', ODTFile)
    # Fill the odt file handler with the namespace dictionnary content.
    document = stl_to_odt(handler, namespace)
    # Save the letter
    handler = ODTFile(string=document)
    rw_database.set_handler('model_letter2.odt', handler)
    rw_database.save_changes()



.. rubric:: Footnotes

.. [#odf-specifications] ODF is ISO/IEC 26300 - http://www.oasis-open.org/committees/download.php/12572/OpenDocument-v1.0-os.pdf


