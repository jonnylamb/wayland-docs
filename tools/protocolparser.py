#
# protocolparser.py
#
# Reads in a protocol document and generates pretty data structures from it.
#
# Copyright (C) 2009-2010 Collabora Ltd.
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or (at
# your option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Authors: Davyd Madeley <davyd.madeley@collabora.co.uk>
#

import os
import sys

import bisect
import itertools

import xml.dom, xml.dom.minidom

class UnknownType(Exception): pass
class BrokenHTML(Exception): pass
class WrongNumberOfChildren(Exception): pass
class TypeMismatch(Exception): pass
class DuplicateEnumValueValue(Exception): pass
class UnknownTag(Exception): pass
class NoCopyright(Exception): pass

def getText(dom):
    try:
        if dom.childNodes[0].nodeType == dom.TEXT_NODE:
            return dom.childNodes[0].data
        else:
            return ''
    except IndexError:
        return ''
    except AttributeError:
        return ''

def getChildrenByName(dom, name):
    return filter(lambda n: n.nodeType == n.ELEMENT_NODE and \
                            n.localName == name,
                  dom.childNodes)

def getChildrenByNameAndAttribute(dom, name, attribute, value):
    return filter(lambda n: n.nodeType == n.ELEMENT_NODE and \
                            n.localName == name and \
                            n.getAttribute(attribute) == value,
                  dom.childNodes)

def getOnlyChildByName(dom, name):
    kids = getChildrenByName(dom, name)

    if len(kids) == 0:
        return None

    if len(kids) > 1:
        raise WrongNumberOfChildren(
            '<%s> node should have at most one <%s/> child' %
            (dom.tagName, name))

    return kids[0]

def getAnnotationByName(dom, name):
    kids = getChildrenByNameAndAttribute(dom, None, 'annotation', 'name', name)

    if len(kids) == 0:
        return None

    if len(kids) > 1:
        raise WrongNumberOfChildren(
            '<%s> node should have at most one %s annotation' %
            (dom.tagName, name))

    return kids[0].getAttribute('value')

class Base(object):
    """The base class for any type of XML node in the protocol that implements the
       'name' attribute.

       Don't instantiate this class directly.
    """
    def __init__(self, parent, dom):
        self.name = name = dom.getAttribute('name')
        self.parent = parent

        self.since = dom.getAttribute('since')
        self.description = getOnlyChildByName(dom, 'description')

        self.refs = []
        self.constructors = []

        for child in dom.childNodes:
            if (child.nodeType == dom.TEXT_NODE and
                    child.data.strip() != ''):

                # http://lists.freedesktop.org/archives/wayland-devel/2014-February/013428.html
                if self.description is None:
                    self.description = child.data.strip()
                else:
                    raise BrokenHTML('Text found in node %s of %s:\n\n%s' %
                        (self.__class__.__name__, self.parent, child.data.strip()))
            elif child.nodeType == dom.ELEMENT_NODE:
                if child.tagName in ('p', 'em', 'strong', 'ul', 'li', 'dl',
                        'a', 'tt', 'code'):
                    raise BrokenHTML('HTML element <%s> found in node %s of %s?' %
                        (child.tagName, self.__class__.__name__, self.parent))

    def check_consistency(self):
        pass

    def get_full_name(self):
        return self.parent.get_full_name() + '.' + self.name

    def get_type_name(self):
        return self.__class__.__name__

    def get_protocol(self):
        return self.parent.get_protocol()

    def get_interface(self):
        return self.parent.get_interface()

    def get_anchor(self):
        return "%s:%s" % (
            self.get_type_name(),
            self.name)

    def get_url(self):
        return "%s#%s" % (self.get_interface().get_url(), self.get_anchor())

    def get_description(self):
        """Get the description for this node.
        """
        if self.description is None:
            return ''
        else:
            if getText(self.description) == '':
                if isinstance(self.description, unicode) and self.description != '':
                    summary = self.description
                else:
                    summary = self.description.getAttribute('summary')
                if summary != '':
                    return '<div class=\'docstring\'>%s</div>' % summary
                else:
                    return ''

            # make a copy of this node, turn it into a HTML <div> tag
            node = self.description.cloneNode(True)
            node.tagName = 'div'
            node.baseURI = None
            node.removeAttribute('summary')
            node.setAttribute('class', 'docstring')

            return self.convert_to_html(node)

    def convert_to_html(self, node):
        protocol = self.get_protocol()
        dom = protocol.document

        lines = [s.strip() for s in getText(node).split('\n')]

        # get rid of rubbish at beginning and end
        while not lines[0]: del lines[0]
        while not lines[-1]: del lines[-1]

        # split lines by empty elements
        paragraphs = [list(group) for k, group in itertools.groupby(lines, bool) if k]

        # remove old text node
        node.removeChild(node.childNodes[0])

        def add_text_node(element, words, padding=False):
            if not words:
                return

            if padding:
                words += ' '

            text = ' '.join(words)
            t = dom.createTextNode(text)
            element.appendChild(t)

        # add anchor tags for stuff we can link to
        def add_wl_links(paragraph, text):
            words = text.split()
            punctuation = '.,!"\''

            current = []
            for i, word in enumerate(words):
                if not word.startswith('wl_'):
                    current += [word]
                    continue

                ending = ''
                if not word[-1].isalpha() and word[-1] in punctuation:
                    ending = word[-1]
                    word = word[:-1]

                t = protocol.lookup(word)
                if t is None:
                    current += [word + ending]
                else:
                    add_text_node(p, current, len(current) > 0)
                    current = []

                    a = dom.createElement('a')
                    a.setAttribute('href', t.get_url())
                    add_text_node(a, [word])
                    p.appendChild(a)

                    current += [ending]

            add_text_node(p, current)

        # add new paragraph nodes
        for text in [' '.join(x) for x in paragraphs]:
            p = dom.createElement('p')
            add_wl_links(p, text)
            node.appendChild(p)

        return node.toxml().encode('ascii', 'xmlcharrefreplace')

    def get_title(self):
        return '%s %s' % (self.get_type_name(), self.name)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.name)

    def get_index_entries(self):
        context = self.name
        return set([
            '%s (%s in %s)' % (self.name, self.get_type_name(), context),
            '%s %s' % (self.get_type_name(), self.name)])

class Request(Base):
    def __init__(self, parent, dom):
        super(Request, self).__init__(parent, dom)

        self.type = dom.getAttribute('type')

        self.args = build_list(self, Arg,
                               dom.getElementsByTagName('arg'))

    def get_args(self):
        return ', '.join(map(lambda a: a.protocol_name(), self.args))

    def check_consistency(self):
        for x in self.args:
            x.check_consistency()

class Typed(Base):
    """The base class for all typed nodes (i.e. Arg).

       Don't instantiate this class directly.
    """

    def __init__(self, parent, dom):
        super(Typed, self).__init__(parent, dom)

        self.type = dom.getAttribute('type')
        self.interface = dom.getAttribute('interface')

    def get_type(self):
        return self.get_protocol().lookup(self.interface)

    def get_type_url(self):
        t = self.get_type()
        if t is None: return ''
        else: return t.get_url()

    def get_type_title(self):
        t = self.get_type()
        if t is None: return ''
        else: return t.get_title()

    def check_consistency(self):
        t = self.get_type()

        if t is None and self.type in ['object', 'new_id']:
            raise TypeMismatch('%r type is \'%s\' but has no interface'
                               % (self, self.type))

        if t is None:
            if self.type not in (
                    # Basic types
                    'int', 'uint', 'fixed', 'string', 'array', 'fd', 'new_id', 'object',
                    ):
                raise UnknownType('%r type "%s" is unknown'
                        % (self, self.type))
        else:
            if self.type not in ['object', 'new_id']:
                raise TypeMismatch('%r is given an interface (%s) but type isn\'t new_id '
                        'or object (it is \'%s\')'
                        % (self, t.name, t, t.type))

    def protocol_name(self):
        return '%s: %s' % (self.type, self.name)

    def __repr__(self):
        return '%s(%s:%s)' % (self.__class__.__name__, self.name, self.type)

class Arg(Typed):
    def __init__(self, parent, dom):
        super(Arg, self).__init__(parent, dom)

        self.summary = dom.getAttribute('summary')
        self.interface = dom.getAttribute('interface')
        self.allow_null = dom.getAttribute('allow-null')

class Event(Base):
    def __init__(self, parent, dom):
        super(Event, self).__init__(parent, dom)

        self.args = build_list(self, Arg,
                               dom.getElementsByTagName('arg'))

    def get_args(self):
        return ', '.join(map(lambda a: a.protocol_name(), self.args))

class Interface(Base):
    def __init__(self, parent, dom):
        super(Interface, self).__init__(parent, dom)

        # build lists of requests, etc., in this interface
        self.requests = build_list(self, Request,
                                  dom.getElementsByTagName('request'))
        self.events = build_list(self, Event,
                                  dom.getElementsByTagName('event'))
        self.enums = build_list(self, Enum,
                                  dom.getElementsByTagName('enum'))

    def get_full_name(self):
        return self.name

    def get_interface(self):
        return self

    def get_summary(self):
        if self.description is None:
            return ''
        else:
            return self.description.getAttribute('summary')

    def get_url(self):
        return '%s.html' % self.name

class EnumEntry(Base):
    def __init__(self, parent, dom):
        super(EnumEntry, self).__init__(parent, dom)

        self.name = dom.getAttribute('name')
        self.value = dom.getAttribute('value')
        self.summary = dom.getAttribute('summary')

class Enum(Base):
    def __init__(self, parent, dom):
        super(Enum, self).__init__(parent, dom)
        self.entries = build_list(self, EnumEntry,
                        dom.getElementsByTagName('entry'))

        self.check_for_duplicates()

    def get_breakdown(self):
        str = ''
        str += '<ul>\n'
        for entry in self.entries:
            str += '<li>%s (%s)</li>\n' % (entry.name, entry.value)
            str += '<div class=\'docstring\'>%s</div>' % entry.summary
        str += '</ul>\n'

        return str

    def check_for_duplicates(self):
        # make sure no two entries have the same value
        for u in self.entries:
            for v in [x for x in self.entries if x is not u]:
                if u.value == v.value:
                    raise DuplicateEnumValueValue('%s %s has two entries '
                            'with the same value: %s=%s and %s=%s' % \
                            (self.__class__.__name__, self.name, \
                             u.name, u.value, v.name, v.value))

class Protocol(object):
    def __init__(self, dom, title):
        self.document = dom
        self.title = title

        # build a list of interfaces in this protocol
        self.interfaces = []
        def recurse(nodes):
            for node in nodes:
                if node.nodeType != node.ELEMENT_NODE: continue

                if node.tagName == 'protocol':
                    # recurse into this level for interesting items
                    recurse(node.childNodes)
                elif node.tagName == 'interface':
                    self.interfaces.append(Interface(self, node))
                elif node.tagName == 'copyright':
                    continue
                else:
                    raise UnknownTag('protocol has unknown child: %s' % \
                                     node.tagName)

        recurse(dom.childNodes)

        self.everything = {}
        for interface in self.interfaces:
            self.everything[interface.get_full_name()] = interface

            for things in [ 'requests', 'events', 'enums' ]:
                for thing in getattr(interface, things):
                    self.everything[thing.get_full_name()] = thing

        # sort out references
        for item in self.everything.values():
            if hasattr(item, 'args'):
                args = getattr(item, 'args')

                for arg in args:
                    t = arg.get_type()
                    if t is None:
                        continue

                    if arg.type == 'new_id':
                        bisect.insort(t.constructors, item)
                    else:
                        bisect.insort(t.refs, item)

        # get some extra bits for the HTML
        node = dom.getElementsByTagNameNS(None, 'protocol')[0]
        self.name = node.getAttribute('name')

    def get_copyright_parts(self):
        proto = self.document.getElementsByTagName('protocol')[0]
        node = getOnlyChildByName(proto, 'copyright')

        if len(node.childNodes) != 1 or \
          node.childNodes[0].nodeType != node.TEXT_NODE:
            raise NoCopyright

        text = node.childNodes[0].data.strip()
        return [x.strip() for x in text.split('\n\n')]

    def get_copyrights(self):
        return [x.strip() for x in self.get_copyright_parts()[0].split('\n')]

    def get_licenses(self):
        return self.get_copyright_parts()[1:]

    def get_protocol(self):
        return self

    def lookup(self, name):
        return self.everything.get(name, None)

    def get_title(self):
        return '%s Protocol' % self.title.capitalize()

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.name)

def build_list(parent, type_, nodes):
    return map(lambda node: type_(parent, node), nodes)

def parse(filename, title):
    if os.path.isdir(filename):
        impl = xml.dom.getDOMImplementation()
        dom = impl.createDocument(None, "protocol", None)
        proto = dom.firstChild
        proto.setAttribute('name', 'wayland')
        copyright = False

        for n in os.listdir(filename):
            if not n.endswith('.xml'):
                continue
            if n.startswith('.'):
                continue

            d = xml.dom.minidom.parse(os.path.join(filename, n))
            p = getOnlyChildByName(d, 'protocol')

            for child in getChildrenByName(p, 'interface'):
                proto.appendChild(child)

            if not copyright:
                c = getOnlyChildByName(p, 'copyright')
                if c is not None:
                    proto.appendChild(c)
                    copyright = True
    else:
        dom = xml.dom.minidom.parse(filename)

    protocol = Protocol(dom, title)

    return protocol

if __name__ == '__main__':
    parse(sys.argv[1])
