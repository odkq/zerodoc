#!/usr/bin/env python
""" 
    zerodoc ascii-art diagrams support
    
    Copyright (C) 2012 Pablo Martin <pablo at odkq.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import cgi
import hashlib
import tempfile
import subprocess

def generate_diagram(buffer, format):
    # Write the buffer into a file
    f = tempfile.NamedTemporaryFile(delete=False, prefix='zero')
    f.write(buffer)
    f.close()
    os.de

def extract_option(options, key)
    for o in options:
        b = o.split(':')
            if len(b) == 2:
                if b[0] == key:
                    return b[1]
    return None

def generate_diagram_ditaa(path, options):
    jarpath = extract_option(options, 'jarpath')
    r = ['java', '-jar', jarpath, path ]
    p = subprocess.Popen(r, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o = p.communicate()[0]
    i = o.find('Rendering to file: ')
    if i == -1:
        print 'Error generating diagram!'
        return None
    j = o[i:].find('\n')
    return o[i+19:i+j]

def write_diagramlines(options, diagramlines):
    if 'rawdiagrams' in options:
        return write_sourcelines(options, diagramlines)
    if not 'datauri' in options:
        if not os.path.exists('images'):
            os.mkdir('images')
        f = tempfile.NamedTemporaryFile(delete=False, prefix='zero', dir='images')
    else:
        f = tempfile.NamedTemporaryFile(delete=False)
    for sline in diagramlines:
        if 'sourceline' in sline:
            f.write(sline['sourceline'] + '\n')
        else:
            print 'unknown element in sourcelines (diagram)' + str(sline) +\
            ' ' + str(sline.keys())
    n = f.name
    f.close()
    dfile = generate_diagram_image(n)
    os.remove(n)
    if dfile == None:
        return ''
    else:
        if not 'datauri' in options:
            return '<img src="' + dfile + '" />\n'
        else:
            # Taken from http://en.wikipedia.org/wiki/Data_URI_scheme#Python
            duri = str(base64.encodestring(open(dfile, "rb").read())).replace("\n", "")
            t = '<img alt="sample" src="data:image/png;base64,{0}">\n'.format(duri)
            os.remove(dfile)
            return t
