itools.rest: an Alternative Implementation of reStructuredText
==============================================================

10 Reasons not to Use docutils
------------------------------

    - Overriding a transformation is at best hypothetical, at worst a hack, say
      thank you to black magic.
    - Unable to write a reference in Chinese.
    - Unable to write a reference inside a strong emphasis.
    - The document tree is not meant to be manipulated but some half-baked XML
      export: the TOC is already computed, dandling references are forcely
      replaced by an error node...
    - The architecture is defective and hard to understand: multiplication of
      classes, thousand-line __init__.py's...
    - The mix of bytestring and unicode with no encoding makes it unreliable to
      write a complete document in anything else than English; don't even dare
      str() or repr() a document or a node in French or Chinese.
    - Docutils is too conservative: say goodbye to Python 2.1 and hello to 2007.
    - Docutils complains where there is a gap in title levels. Are LaTeX or Web
      browsers complaining?
    - Cannot merge two documents easily, partly because of the TOC issue above.
    - Conversion may fail just because one character is missing in the title
      underline. Docutils is generally too strict.


.. vim:tw=80:ft=rst
