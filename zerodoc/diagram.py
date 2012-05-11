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

def extract_option(options, key):
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

def generate_diagram_aafigure(path, options):
    jarpath = extract_option(options, '')
    # aafigure diagram -t svg -o diagram.svg
    if 'svg' in options:
        outpath = path + '.svg'
        r = ['aafigure', path, '-t', 'svg', '-o', outpath]
    else:
        outpath = path + '.png'
        r = ['aafigure', path, '-t', 'png', '-o', outpath]
    p = subprocess.Popen(r, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o = p.communicate()[0]
    return outpath

# get_diagram_ditaa:
# Return the diagram bitmap in a buffer
def get_diagram_ditaa(options, lines):
    f = tempfile.NamedTemporaryFile(delete=False)
    for line in lines:
        f.write(line + '\n')
    f.close()
    n = f.name
    if 'ditaa' in options:
        dfile = generate_diagram_ditaa(n, options)
    elif 'aafigure' in options:
        dfile = generate_diagram_aafigure(n, options)
    else:
        print 'Specify a conversor for diagrams! (ditaa or aafigure)'
        return None
    os.remove(n)
    if dfile == None:
        return None
    f = open(dfile, 'r')
    r = f.read()
    f.close()
    return r

