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
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Preformatted)
from reportlab.platypus.flowables import Flowable, HRFlowable


__tab_para_alignment = {'LEFT': TA_LEFT, 'RIGHT': TA_RIGHT,
                        'CENTER': TA_CENTER, 'JUSTIFY': TA_JUSTIFY}
TAG_NOT_SUPPORTED = '%s: line %s tag "%s" is currently not supported.'
WARNING_DTD = '%s: line %s tag "%s" is unapproprieted here.'
encoding = 'UTF-8'


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
    alias_style = {}
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
            elif tag_name == 'head':
                a = 2
            elif tag_name == 'body':
                story += body_stream(stream, tag_uri, tag_name, attributes,
                                     alias_style)
            else :
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'html':
                break
            if tag_name == 'head':
                continue
            else:
                # unknown tag
                stack.pop()

    #### BUILD PDF ####
    # rml attribute != reportlab attribute --> pageSize
    document_attrs['pagesize'] = document_attrs['pageSize']

    if is_test == True:
        _story = list(story)

    #print story

    doc = SimpleDocTemplate(document_name + ".pdf", pagesize = letter)
    doc.build(story)

    if is_test == True:
        return (_story, pdf_stylesheet)


def body_stream(stream, _tag_uri, _tag_name, _attributes, alias_style):
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
            elif tag_name == 'pre':
                story.append(pre_stream(stream, tag_uri, tag_name, attributes, pdf_stylesheet))
            elif tag_name in ['h1','h2','h3']:
                story.append(heading_stream(stream, tag_uri, tag_name,
                            attributes, pdf_stylesheet, alias_style))
            elif tag_name == 'hr':
                story.append(hr_stream(stream, tag_uri, tag_name, attributes))
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'body':
                break
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))
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
            if tag_name == 'p':
                print WARNING_DTD % ('document', line_number, tag_name)
            elif tag_name in ['i', 'em']:
                content.append("<i>")
            elif tag_name in ['b', 'strong']:
                content.append("<b>")
            elif tag_name == 'u':
                content.append("<u>")
            elif tag_name == 'sup':
                content.append("<super>")
            elif tag_name == 'sub':
                content.append("<sub>")
            elif tag_name == 'br':
                continue
            elif tag_name == 'ol':
                content += ol_stream(stream, tag_uri, tag_name, attributes, pdf_stylesheet)
            elif tag_name == 'ul':
                content += ul_stream(stream, tag_uri, tag_name, attributes, pdf_stylesheet)
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'p':
                return create_paragraph(pdf_stylesheet, {}, stack.pop(), content)
            elif tag_name in ['i', 'em']:
                content.append("</i>")
            elif tag_name in ['b', 'strong']:
                content.append("</b>")
            elif tag_name == 'u':
                content.append("</u>")
            elif tag_name == 'sup':
                content.append("</super>")
            elif tag_name == 'sub':
                content.append("</sub>")
            elif tag_name == 'br':
                content.append("<br/>")
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


def pre_stream(stream , tag_uri, tag_name, attributes, pdf_stylesheet):
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
            print WARNING_DTD % ('document', line_number, tag_name)
            stack.append((tag_name, attributes, None))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'pre':
                return create_preformatted(pdf_stylesheet, {}, stack.pop(), content)
            else:
                print WARNING_DTD % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if stack:
                # we dont strip the string --> preformatted widget
                value = XML.encode(Unicode.decode(value, encoding)) # entities
                content.append(value)


def heading_stream(stream, _tag_uri, _tag_name, _attributes, pdf_stylesheet,
                   alias_style):
    """
        Create a heading widget.
    """

    content = []
    stack = []
    stack.append((_tag_name, _attributes, None))
    style = get_style(pdf_stylesheet, alias_style,  _tag_name)

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            print WARNING_DTD % ('document', line_number, tag_name)
            stack.append((tag_name, attributes, None))
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                content = ''.join(content)
                widget = Paragraph(content, style)
                return widget
            else:
                print WARNING_DTD % ('document', line_number, tag_name)
                element = stack.pop()

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if stack:
                value = normalize(Unicode.decode(value, encoding), True)
                if len(value) > 0 and value != ' ':
                    value = XML.encode(value) # entities
                content.append(value)
                has_content = True


def hr_stream(stream, _tag_uri, _tag_name, _attributes):
    """
        Create a hr widget.
    """
    stack = []
    stack.append((_tag_name, _attributes, None))
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            stack.append((tag_name, attributes, None))
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                widget = create_hr(_attributes)
                return widget
            else:
                element = stack.pop()
        #### TEXT ELEMENT ####
        elif event == TEXT:
            pass


def ol_stream(stream , tag_uri, tag_name, attributes, pdf_stylesheet):
    #TODO Fix the space at the begining of a new list-lign
    stack = []
    story = []
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    content = []
    has_content = False
    stack.append((tag_name, attributes, None))
    attrs = {}
    if exist_attribute(attributes, ['type']):
      attrs['type'] = attributes.get((None,'type')).lower()
      if attrs['type'] == 'upper roman':
        content.append("<seqFormat value='I'></seq>")
      if attrs['type'] == 'lower roman':
        content.append("<seqFormat value='i'></seq>")
      if attrs['type'] == 'lower alpha':
        content.append("<seqFormat value='a'></seq>")
      if attrs['type'] == 'upper alpha':
        content.append("<seqFormat value='A'></seq>")
      else:
        content.append("<seqFormat value='1'></seq>")
    else:
      content.append("<seqFormat value='1'></seq>")

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'ol':
                print WARNING_DTD % ('document', line_number, tag_name)
            elif tag_name == 'li':
                content.append("<seq> ")
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'ol':
                return content
            elif tag_name in ['i', 'em']:
                content.append("</i>")
            elif tag_name in ['b', 'strong']:
                content.append("</b>")
            elif tag_name == 'u':
                content.append("</u>")
            elif tag_name == 'sup':
                content.append("</super>")
            elif tag_name == 'sub':
                content.append("</sub>")
            elif tag_name == 'li':
                content.append("</seq><br/>")
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


def ul_stream(stream , tag_uri, tag_name, attributes, pdf_stylesheet):
    #TODO Fix the space at the begining of a new list-lign
    stack = []
    story = []
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    content = []
    has_content = False
    stack.append((tag_name, attributes, None))
    content.append("<br/>")

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'ul':
                print WARNING_DTD % ('document', line_number, tag_name)
            elif tag_name == 'li':
                content.append('- ')
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'ul':
                return content
            elif tag_name in ['i', 'em']:
                content.append("</i>")
            elif tag_name in ['b', 'strong']:
                content.append("</b>")
            elif tag_name == 'u':
                content.append("</u>")
            elif tag_name == 'sup':
                content.append("</super>")
            elif tag_name == 'sub':
                content.append("</sub>")
            elif tag_name == 'li':
                content.append("<br/>")
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
            if key == 'align':
                key = 'alignment'
            if key == 'alignment':
                attr_value = __tab_para_alignment.get(attr_value.upper())
            elif key in ['leftIndent', 'rightIndent']:
                attr_value = rml_value(attr_value)
            style_attr[key] = attr_value

    style_name = parent_style
    parent_style = get_style(pdf_stylesheet, alias_style, parent_style)
    style = ParagraphStyle(style_name, parent=parent_style, **style_attr)
    return Paragraph(content, style, bulletText)


def create_preformatted(pdf_stylesheet, alias_style, element, content):
    """
        Create a reportlab preformatted widget.
    """

    content = ''.join(content)
    style_name = 'Normal'

    for key, attr_value in element[1].iteritems():
        if key[1] == 'style':
            style_name = attr_value

    if element[0] == 'pre':
        fn = Preformatted

    style = get_style(pdf_stylesheet, alias_style, style_name)

    widget = fn(content, style)
    return widget


def build_start_tag(tag_name, attributes):
    """
        Create the XML start tag from his name and his attributes
    """

    attr_str = ''.join([' %s="%s"' % (key[1], attributes[key])
                        for key in attributes.keys()])
    return '<%s%s>' % (tag_name, attr_str)


def build_end_tag(tag_name):
    """
        Create the XML end tag from his name.
    """

    return '</%s>' % tag_name


def create_hr(attributes):
    """
        Create a reportlab hr widget
    """

    attrs = {}
    attrs['width'] = "100%"
    for key in ['width', 'thickness', 'spaceBefore', 'spaceAfter']:
        if exist_attribute(attributes, [key]):
            attrs[key] = rml_value(attributes.get((None, key)))
    if exist_attribute(attributes, ['lineCap']):
        line_cap = attributes.get((None,'lineCap'))
        if line_cap not in ['butt', 'round', 'square']:
            line_cap = 'butt'
        attrs['lineCap'] = line_cap
    if exist_attribute(attributes, ['color']):
        attrs['color'] = get_color(attributes.get((None, 'color')))
    if exist_attribute(attributes, ['align']):
        hAlign = attributes.get((None, 'align'), '').upper()
        if hAlign in ['LEFT', 'RIGHT', 'CENTER', 'CENTRE']:
            attrs['hAlign'] = hAlign
    if exist_attribute(attributes, ['vAlign']):
        vAlign = attributes.get((None, 'vAlign'), '').upper()
        if vAlign in ['TOP', 'MIDDLE', 'BOTTOM']:
            attrs['vAlign'] = vAlign
    return HRFlowable(**attrs)


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


def exist_attribute(attrs, keys):
    """
        Return True if all key in keys
        are contained in the dictionnary attrs
    """

    for key in keys:
        if attrs.has_key((None, key)) == False:
            return False
    return True


def rml_value(value, default=None):
    """
       Return the reportlab value of value
       only if value is a string
       '2cm' -> 2 * cm
       '2in' -> 2 * inch
       '2in' -> 2 * mm
       '2in' -> 2 * pica
       '2%' -> '2%'
    """
    if value is None:
        return default

    coef = 1
    if not is_str(value):
        return value

    value = value.strip()
    if value == "None":
        return None
    if value[-2:] == 'in':
        coef = inch
        value = value[:-2]
    elif value[-2:] == 'cm':
        coef = cm
        value = value[:-2]
    elif value[-2:] == 'mm':
        coef = mm
        value = value[:-2]
    elif value[-4:] == 'pica':
        coef = pica
        value = value[:-4]

    elif value[-1:] == '%':
        return value

    try:
        value = float(value) * coef
    except ValueError:
        value = default
    return value


def is_str(str, check_is_unicode=True):
    """
        Check is str is a string.
    """

    if type(str) != type(''):
        if not check_is_unicode:
            return False
        return type(str) == type(u'')
    return True

