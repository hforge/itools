"""
graphication.css:

  A lightweight, simplified-CSS parser and matcher.

Implements element-, id- and class-based selecting/matching.
All properties inherit by default, and there's no support for the 'inherit'
keyword.

Any @media, @import, etc. parts are also entirely useless. As is !important.

Copyright Andrew Godwin, 2007
Released under the terms of the GPL, version 3.

$Id: css.py 45 2007-11-29 17:40:52Z andrew $
"""

from UserDict import UserDict

import sys
from os.path import isdir, join, exists, abspath


def selector_split(string, single_class=True):

    """
    Turns a selector-ish string into a list of (tag, id, class) tuples.
    If single_class is False, class is a list of classes rather than a string.

    @param string: The seleector string to parse.
    @type string: str

    @param single_class: Whether to return lists of classes (False)
        or a single class (True).
    @type single_class: bool
    """

    bits = string.split()
    details = []

    for bit in bits:
        if "#" in bit:
            tag, idcls = bit.split("#", 1)
            idcls = idcls.split(".")
            id = idcls[0]
            cls = idcls[1:]
        else:
            id = None
            tagcls = bit.split(".")
            tag = tagcls[0]
            cls = tagcls[1:]

        # Allow for tag wildcards
        if tag == "*":
            tag = None

        # Make sure we use None for non-existence
        tag = tag or None
        id = id or None

        if single_class:
            if len(cls):
                cls = cls[0]
            else:
                cls = None

        details.append((tag, id, cls))

    return details



def hex_to_rgba(color):

    """
    Converts a hex colour to a RGBA sequence.
    If passed an RGBA sequence, will return it normally.

    @param color: The color to translate.
    @type color: str, 4-tuple or 4-list
    """

    if not isinstance(color, str) or isinstance(color, unicode):
        try:
            r,g,b,a = color
            return r,g,b,a
        except (TypeError, ValueError):
            pass

    color = color.replace("#", "")

    if len(color) in [3,4]:
        color = "".join([c*2 for c in color])

    hex_r, hex_g, hex_b = color[:2], color[2:4], color[4:6]
    hex_a = color[6:8]
    if not hex_a:
        hex_a = "ff"

    return map(lambda x: int(x, 16)/255.0, [hex_r, hex_g, hex_b, hex_a])



class CssSelector(object):

    """
    Represents a CSS selector, as well as performing useful selector-related
    tasks.
    """


    def __init__(self, details):

        """
        Constructor.

        @param details: The 'details' (list of (tag, id, class) tuples) to use
        @type details: list
        """

        # Details is a list of (element, id, class) tuples. One or more of
        # each can be None.
        self.details = details
        self.calculate_specificity()


    def __repr__(self):
        return "<CssSelector %s>" % self.details


    def detail_to_str(self, detail):

        """
        Turns a single detail into a part of a CSS textual selector.
        i.e. ("grid", None, "first") -> 'grid.first'

        @param detail: The detail to stringify
        @type detail: tuple
        """

        s = detail[0] or "*"
        if detail[1]:
            s += "#" + detail[1]
        if detail[2]:
            s += "." + detail[2]
        return s


    def __str__(self):
        return " ".join(map(self.detail_to_str, self.details))


    @classmethod
    def from_string(self, string):

        """
        Alternate constructor; initialises from a CSS selector string.

        @param string: The CSS selector string to initialise from.
        @type string: str
        """

        details = selector_split(string, True)
        return self(details)


    def calculate_specificity(self):

        """
        Caculates the specificity of this selector (see CSS spec for details).
        """

        self.specificity = [0,0,0]
        for element, id, cls in self.details:
            if element is not None:
                self.specificity[1] += 1
            if id is not None:
                self.specificity[0] += 1
            if cls is not None:
                self.specificity[2] += 1


    def matches(self, element_rep):
        """
        Sees if this selector matches the given 'element representation'.
        This is a list of (element, id, [classes]) tuples.

        @param element_rep: The element representation to match.
                            A list of (tag, id, [classes]) tuples.
        @type element_rep: list
        """

        di = 0

        for element, id, clss in element_rep:
            curr_det = self.details[di]
            if curr_det[0] in [element, None]:
                if curr_det[1] in [id, None]:
                    if curr_det[2] in clss + [None]:
                        di += 1
                        if di >= len(self.details):
                            return True

        return di >= len(self.details)



class CssRule(object):

    """
    Represents a single CSS rule.
    Has a selector, and a dictionary of properties.
    """

    d_shortcuts = {
            "padding": ["-top", "-right", "-bottom", "-left"],
            "margin": ["-top", "-right", "-bottom", "-left"],
    }


    def __init__(self, selector, properties={}):

        """
        Constructor.

        @param selector: The selector to use for this rule. You can pass
                         either a CSS selector string or a CssSelector.
        @type selector: str or CssSelector
        """

        if isinstance(selector, str) or isinstance(selector, unicode):
            selector = CssSelector.from_string(selector)

        assertion = "The selector must be a CssSelector or a string."
        assert isinstance(selector, CssSelector), assertion

        self.selector = selector
        self.properties = properties

        self.check_shortcuts()


    def check_shortcuts(self):
        # For each 'distance shortcut'...
        for d_shortcut, items in self.__class__.d_shortcuts.items():
            # If it exists, apply its values as defaults
            if d_shortcut in self.properties:
                properties = self.properties[d_shortcut].split()
                values = filter(lambda x:bool(x.strip()), properties)
                for item in items:
                    self.properties[d_shortcut+item] = self.properties.get(
                                d_shortcut+item,
                                    values[items.index(item) % len(values)]
                        )


    def __repr__(self):
        return "<CssRule; %i properties, selector %s>" % (len(self.properties), self.selector)



class CssProperties(UserDict):

    """
    Like a dictionary, except it has things like get_int and get_list methods.
    """


    def get_int(self, key, default=0):
        """Like dict.get, but coerces the result to an integer."""
        return int(self.get(key, default))


    def get_float(self, key, default=0):
        """Like dict.get, but coerces the result to a float."""
        return float(self.get(key, default))


    def is_auto(self, key, default=True):
        """Returns if the given field has the special 'auto' value or not."""
        try:
            return self[key].lower() == "auto"
        except KeyError:
            return default


    def get_list(self, key, default=[]):
        """Like dict.get, but splits the result as a comma-separated list."""
        return [x.strip() for x in self.get(key, default).split(",")]


    def get_fraction(self, key, default=0.5):
        """Like dict.get, but always returns a number between 0 and 1.
        Correctly interprets 'top', 'left', 'middle', 'center', etc., as well
        as percentages."""

        val = self.get(key, default)
        # Try percentages or keywords
        if isinstance(val, str) or isinstance(val, unicode):
            if val[-1] == "%":
                val = float(val[:-1]) / 100.0
            else:
                try:
                    val = float(val)
                except ValueError:
                    val = {
                            "left": 0.0,
                            "top": 0.0,
                            "middle": 0.5,
                            "center": 0.5,
                            "centre": 0.5,
                            "bottom": 1.0,
                            "right": 1.0,
                            "zero": 0.0,
                            "half": 0.5,
                            "full": 1.0,
                            "all": 1.0,
                            "quarter": 0.25,
                            "three-quarters": 0.75,
                            "none": 0.0,
                    }[val]

        # Make sure it's valid
        try:
            val = float(val)
        except ValueError:
            text_error = "Invalid value for alignment key '%s': %s"
            raise ValueError(text_error % (key, val))

        #assert (val >= 0) and (val <= 1), "Alignment key '%s' must have a
        #value between 0 and 1, not %s." % (key, val)

        return val
    get_align = get_fraction


    def get_color(self, key="color", default="#000"):
        """Like dict.get, but parses the result as a colour
        (#xxx, #xxxx, #xxxxxx or #xxxxxxxx) and returns a (r,g,b,a) tuple."""
        color = self.get(key, default)
        color = hex_to_rgba(color)
        return color


    def get_font_weight(self, key="font-weight", default="normal"):
        """Like dict.get, but normalises the value into a font weight."""
        weight = self.get(key, default).lower()
        return weight


    def get_cairo_font_weight(self, key="font-weight", default="normal"):
        """Like dict.get, but returns the value as a Cairo font weight."""

        weight = self.get_font_weight(key, default)

        import cairo
        return {
                "normal": cairo.FONT_WEIGHT_NORMAL,
                "bold": cairo.FONT_WEIGHT_BOLD,
        }[weight]


    def get_font_style(self, key="font-style", default="normal"):
        """Like dict.get, but normalises the value into a font style."""
        weight = self.get(key, default).lower()
        return weight


    def get_cairo_font_style(self, key="font-style", default="normal"):
        """Like dict.get, but returns the value as a Cairo font style."""

        style = self.get_font_style(key, default)

        import cairo
        return {
                "normal": cairo.FONT_SLANT_NORMAL,
                "italic": cairo.FONT_SLANT_ITALIC,
        }[style]


    def get_font(self, key="font-family", default=None):
        """Like dict.get, but will pick the first font in the
        result list that exists, and fall back to a sensible
        default otherwise."""

        fonts = self.get_list(key)

        # TODO: Detect if a font exists on the system or not.
        for font in fonts:
            return font

        if default:
            return default
        else:
            # TODO: Platform-specific default fonts.
            return "Sans"


    def get_properties(self, element):

        """
        Returns the properties for the element 'element' below this one.

        @param element: An element-list of (tag, id, [classes]) tuples
        @type element: list
        """

        return self.stylesheet.get_properties(self.root + element)


    def get_properties_str(self, element_str):

        """
        Returns the properties for the element 'element' below this one,
        using a selector-like shorthand syntax for the element.

        @param element: A CSS-selector like string(can have .multiple.classes)
        @type element: str
        """

        element = selector_split(element_str, False)
        return self.get_properties(element)


    # Useful shorthands
    sub = props = get_properties_str



class CssStylesheet(object):

    """
    Contains none or more CssRules.
    You can add or remove rules, or pass in element names
    to see what properties it gets.
    """


    def __init__(self):

        """
        Constructor. Takes no arguments, initialises to an empty stylesheet.
        """

        self.rules = []


    def add_rule(self, rule):

        """
        Adds the given rule to the CssStylesheet.

        @param rule: The rule to add.
        @type rule: CssRule
        """

        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.selector.specificity)


    def get_properties(self, element):

        """
        Returns the properties for the element 'element'.

        @param element: An element-list of (tag, id, [classes]) tuples
        @type element: list
        """

        # To stop recursion, and also a sensible fallback
        if not element:
            return {}

        # Recurse to get inherited properties
        properties = self.get_properties(element[:-1])

        # Find matching rules (they're already in order of specificity)
        for rule in self.rules:
            if rule.selector.matches(element):
                properties.update(rule.properties)

        props = CssProperties(properties)
        props.stylesheet = self
        props.root = element
        return props


    def get_properties_str(self, element_str):

        """
        Returns the properties for the element 'element', using a
        selector-like shorthand syntax for the element.

        @param element: A CSS-selector like string(can have .multiple.classes)
        @type element: str
        """

        element = selector_split(element_str, False)
        return self.get_properties(element)


    # Useful shorthands
    __getitem__ = props = get_properties_str


    def merge(self, stylesheet=None):

        """
        Merges this stylesheet with the other one, with the other
        stylesheet's rules taking preference.

        Returns the resulting merged stylesheet.

        Note: DOES NOT update this stylesheet.

        If the stylesheet parameter is None, returns a copy of this
        stylesheet.

        @param stylesheet: The stylesheet to update from.
        @type stylesheet: CssStylesheet
        """

        # TODO: A more sophisticated update that removes duplicates.
        new_stylesheet = CssStylesheet()
        if stylesheet is None:
            new_stylesheet.rules = self.rules + []
        else:
            new_stylesheet.rules = self.rules + stylesheet.rules
        new_stylesheet.rules.sort(key=lambda r: r.selector.specificity)
        return new_stylesheet


    def __repr__(self):
        return "<CssStylesheet; %i rules>" % len(self.rules)


    def __iter__(self):
        return iter(self.rules)


    @classmethod
    def from_css(cls, css):
        """
        Alternate constructor; creates a CssStylesheet from a CSS string.

        @param css: The css stylesheet to parse.
        @type css: str
        """

        self = cls()
        self.load_css(css)
        return self


    def load_css(self, css):
        """
        Parses a CSS string and adds the rules it contains.

        @param css: The css stylesheet to parse.
        @type css: str
        """

        # Initialise loop vars
        in_comment = in_declaration = False
        buffer = ""
        key = value = None

        # Read the css one character at a time
        while css:
            buffer += css[0]
            css = css[1:]

            # If we're not in a comment, do stuff
            if not in_comment:

                # Start a comment?
                if buffer[-2:] == "/*":
                    in_comment = True

                # We might be outside a declaratin...
                elif not in_declaration:

                    # Are we starting a declaration?
                    if buffer[-1] == "{":
                        selector = buffer[:-1].strip()
                        properties = {}
                        buffer = ""
                        in_declaration = True

                # ...or outside one...
                elif in_declaration:

                    # Are we ending here?
                    if buffer[-1] == "}":
                        value = buffer[:-1].strip()
                        if key:
                            properties[key] = value
                        self.add_rule(CssRule(selector, properties))
                        buffer = ""
                        key = value = None
                        in_declaration = False

                    # Moving from a key to a value?
                    elif buffer[-1] == ":":
                        key = buffer[:-1].strip()
                        buffer = ""

                    # Ending a property?
                    elif buffer[-1] == ";":
                        value = buffer[:-1].strip()
                        properties[key] = value
                        buffer = ""
                        key = value = None

            # All we can do is exit a comment.
            else:
                if buffer[-2:] == "*/":
                    in_comment = False
                    buffer = ""



class CssImporter(object):

    """
    Magical importer for CSS files. Should be stuck in sys.meta_path.
    """

    exts = [".css"]

    def find_module(self, fullname, path=None):

        name = fullname.split('.')[-1]
        if name[-4:] == "_css":
            name = name[:-4]

        # Get our paths
        paths = sys.path
        if path:
            paths = path + paths

        # Search 'em
        for path in paths:
            path = abspath(path)
            if isdir(path):
                path = join(path, name)
                for ext in self.exts:
                    if exists(path + ext):
                        self.filename = path + ext
                        return self

        return None


    def load_module(self, fullname):
        stylesheet = CssStylesheet.from_css(open(self.filename).read())
        return stylesheet


    @classmethod
    def install(cls):
        """
        Installs the import hook so that CSS files can be imported using the
        'import' command."""
        sys.meta_path.append(cls())


    @classmethod
    def uninstall(cls):
        """Uninstalls the import hook."""
        sys.meta_path = [x for x in sys.meta_path if not isinstance(x, cls)]


def install_hook():
    """Installs the import hook."""
    CssImporter.install()
