#!/usr/bin/env python
#
# doc-generator.py
#
# Generates HTML documentation from the parsed protocol using Cheetah templates.
#
# Copyright (C) 2009 Collabora Ltd.
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

import sys
import os
import os.path
import shutil

try:
    from Cheetah.Template import Template
except ImportError, e:
    print >> sys.stderr, e
    print >> sys.stderr, "Install `python-cheetah'?"
    sys.exit(-1)

import protocolparser

program, protocol_dir, output_path, title = sys.argv

template_path = os.path.join(os.path.dirname(program), '../doc/templates')

# make the output path
try:
    os.mkdir(output_path)
except OSError:
    pass

# copy in the static files
static = [ 'style.css',
           'jquery.min.js',
           'ui-icons_222222_256x240.png',
           'favicon.png'
         ]
for s in static:
    shutil.copy(os.path.join(template_path, s), output_path)

def load_template(filename):
    try:
        file = open(os.path.join(template_path, filename))
        template_def = file.read()
        file.close()
    except IOError, e:
        print >> sys.stderr, "Could not load template file `%s'" % filename
        print >> sys.stderr, e
        sys.exit(-1)

    return template_def

protocol = protocolparser.parse(protocol_dir, title)

# write out HTML files for each of the interfaces

# Not using render_template here to avoid recompiling it n times.
namespace = { 'protocol': protocol }
template_def = load_template('interface.html')
t = Template(template_def, namespaces = [namespace])
for interface in protocol.interfaces:
    namespace['interface'] = interface

    # open the output file
    out = open(os.path.join(output_path, '%s.html'
        % interface.name), 'w')
    print >> out, unicode(t).encode('utf-8')
    out.close()

def render_template(name, namespaces, target=None):
    if target is None:
        target = name

    namespace = { 'protocol': protocol }
    template_def = load_template(name)
    t = Template(template_def, namespaces=namespaces)
    out = open(os.path.join(output_path, target), 'w')
    print >> out, unicode(t).encode('utf-8')
    out.close()

namespaces = { 'protocol': protocol }

render_template('interfaces.html', namespaces)
render_template('fullindex.html', namespaces)

# write out the TOC last, because this is the file used as the target in the
# Makefile.
render_template('index.html', namespaces)
