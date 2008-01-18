# Import from the Standard Library
from cStringIO import StringIO

# Import from itools
from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, TEXT, CDATA
from itools.datatypes import Unicode, XML

#Import from the reportlab Library
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch, cm, mm, pica
from reportlab.lib.pagesizes import (letter, legal, elevenSeventeen, A0, A1,
    A2, A3, A4, A5, A6, B0, B1, B2, B3, B4, B5, B6, landscape, portrait)
from reportlab.platypus import (Paragraph, SimpleDocTemplate)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

TAG_NOT_SUPPORTED = '%s: line %s tag "%s" is currently not supported.'
encoding = 'UTF-8'

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

def rmltopdf(filename):
    file = open(filename, 'r')
    stream = XMLParser(file.read())
    return document_stream(stream, StringIO(), filename, False)

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
                a = 1
#                p = create_pdf(document_name + ".pdf")
#                stack.append((tag_name, attributes, None))
#            elif tag_name == 'head':

            elif tag_name == 'body':
                story += body_stream(stream, tag_uri, tag_name, attributes)

            else :
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'html':
                break
            else:
                # unknown tag
                stack.pop()

    #### BUILD PDF ####
    # rml attribute != reportlab attribute --> pageSize
    document_attrs['pagesize'] = document_attrs['pageSize']

    if is_test == True:
        _story = list(story)

    print story

    doc = SimpleDocTemplate(document_name + ".pdf", pagesize = letter)
    doc.build(story)

    if is_test == True:
        return (_story, pdf_stylesheet)


def body_stream(stream, _tag_uri, _tag_name, _attributes):
    """
        stream : parser stream
    """
    stack = []
    pdf_stylesheet = getSampleStyleSheet()
    story = []
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break

        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'p':
                story.append(p_stream(stream, tag_uri, tag_name, attributes, pdf_stylesheet))
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))   

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'body':
                break

    #return 1
    return story

def p_stream(stream , tag_uri, tag_name, attributes, pdf_stylesheet):
    stack = []
    story = []
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    content = []
    has_content = False
    stack.append((tag_name, attributes, None))

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            continue 

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'p':
                return create_paragraph(pdf_stylesheet, {}, stack.pop(), content)
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))   

        #### TEXT ELEMENT ####        
        elif event == TEXT:
            value = normalize(Unicode.decode(value, encoding), True)
            if len(value) > 0:
                # alow to write :
                # <para><u><i>foo</i> </u></para>
                value = XML.encode(value) # entities
                if has_content and content[-1] == '</br>':
                    value = value.lstrip()
                content.append(value)
                has_content = True


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


def normalize(data, least=False):
    """
        Normalize data
    """

    if least == True:
        data = u'X%sX' % data
    # we normalize the string
#    data = u' '.join(data.split())
    if least == True:
        return data[1:-1]
    return data

    
def create_paragraph(pdf_stylesheet, alias_style, element, content):
    """
        Create a reportlab paragraph widget.
    """

    parent_style = 'Normal'
    style_attr = {}
    content = ''.join(content)
    bulletText = None

    for key, attr_value in element[1].iteritems():
        key = key[1]
        if key == 'style':
            parent_style = attr_value
        elif key == 'bulletText':
            bulletText = attr_value
        else:
            if key == 'alignment':
                attr_value = __tab_para_alignment.get(attr_value.upper())
            elif key in ['leftIndent', 'rightIndent']:
                attr_value = rml_value(attr_value)
            style_attr[key] = attr_value

    style_name = parent_style
    parent_style = get_style(pdf_stylesheet, alias_style, parent_style)
    style = ParagraphStyle(style_name, parent=parent_style, **style_attr)
    return Paragraph(content, style, bulletText)



def get_style(stylesheet, alias, name):
    """
       Return the style corresponding to name or the style normal if it does
       not exist.
    """

    if name[:6] == 'style.':
        # <alias id="bt" value="style.BodyText"/>
        name = name[6:]

    # we use try except because StyleSheet1 class has no attribute 'get'
    try:
        style = stylesheet[name]
        return style
    except KeyError:
        try:
            style = stylesheet[alias[name]]
            return style
        except KeyError:
            return stylesheet['Normal']


