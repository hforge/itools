# Import from the Standard Library
from cStringIO import StringIO

# Import from itools
from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, TEXT, CDATA

#Import from the reportlab Library
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch, cm, mm, pica
from reportlab.lib.pagesizes import (letter, legal, elevenSeventeen, A0, A1,
    A2, A3, A4, A5, A6, B0, B1, B2, B3, B4, B5, B6, landscape, portrait)


TAG_NOT_SUPPORTED = '%s: line %s tag "%s" is currently not supported.'

def create_pdf(name):
    """
        return a new pdf document using out.pdf as name if no name is provided 
    """
    if name == "":
        name = "out.pdf"
    return Canvas(name)

def save_pdf(p):
    p.showPage()

def close_pdf(p):
    p.save()

def rmltopdf_test(filename):
    file = open(filename, 'r')
    stream = XMLParser(file.read())
    return document_stream(stream, StringIO(), filename, True)

def document_stream(stream, pdf_stream, document_name, is_test=False):
    """
        stream : parser stream
        pdf_stream : reportlab write the pdf into pdf_stream.
        document_name : name of the source file
        Childs : template, stylesheet, story
    """

    document_attrs = { 'leftMargin': inch, 'rightMargin': inch,
                       'topMargin': inch, 'bottomMargin': inch,
                       'pageSize': A4, 'title': None,
                       'author': None, 'rotation': 0,
                       'showBoundary': 0, 'allowSplitting': 1,
                     }

#    pdf_stylesheet = getSampleStyleSheet()
#    pdf_table_style = {}
    # tag alias
    # Aliases allow you to assign more than one name to a paragraph style.
#    alias_style = {}
#    page_templates = []
    stack = []
    story = []
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'html':
                p = create_pdf(document_name + ".pdf")
#                pdf_filename = attributes.get((None, 'filename'), 'noname.pdf')
                stack.append((tag_name, attributes, None))
            elif tag_name == 'p':
                
                
#            elif tag_name == 'docinit':
#                docinit_stream(stream, tag_uri, tag_name, attributes)
#            elif tag_name == 'template':
#                page_templates = template_stream(stream, tag_uri, tag_name,
#                                attributes, document_attrs)
#            elif tag_name == 'stylesheet':
#                alias_style = stylesheet_stream(stream, tag_uri, tag_name,
#                                                attributes, pdf_stylesheet,
#                                                pdf_table_style, alias_style)
#            elif tag_name == 'story':
#              story = story_stream(stream, tag_uri,tag_name, attributes,
#                                   pdf_stylesheet, pdf_table_style,
#                                   alias_style)
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'document':
                break
            else:
                # unknown tag
                stack.pop()

    #### BUILD PDF ####
    # rml attribute != reportlab attribute --> pageSize
    document_attrs['pagesize'] = document_attrs['pageSize']

    if is_test == True:
        _story = list(story)

#    doc.build(story)

    save_pdf(p)
    close_pdf(p)

    if is_test == True:
        return 1 #(_story, pdf_stylesheet)


#######################################################################
## Functions

def stream_next(stream):
    """
        return the next value of the stream
        (event, value, line_number)
        or
        (None, None, None) if StopIteration exception is raised
    """

    try:
        event, value, line_number = stream.next()
        return (event, value, line_number)
    except StopIteration:
        return (None, None, None)

