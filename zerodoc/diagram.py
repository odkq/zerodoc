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
import rsvg
import string
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
    if jarpath == None:
        r = ['ditaa', path ]
    else:
        r = ['java', '-jar', jarpath, path ]
    p = subprocess.Popen(r, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o = p.communicate()[0]
    i = o.find('Rendering to file: ')
    if i == -1:
        print 'Error generating diagram!'
        return None
    j = o[i:].find('\n')
    return o[i+19:i+j], 'png'

def generate_diagram_aafigure(path, options):
    # aafigure diagram -t svg -o diagram.svg
    if 'svg' in options:
        ext = 'svg'
        outpath = path + '.svg'
        r = ['aafigure', path, '-t', 'svg', '-o', outpath]
    else:
        ext = 'png'
        outpath = path + '.png'
        r = ['aafigure', path, '-t', 'png', '-o', outpath]
    p = subprocess.Popen(r, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o = p.communicate()[0]
    return outpath, ext

def generate_diagram_a2s(path, options):
    # aafigure diagram -t svg -o diagram.svg
    outpath = path + '.svg'
    r = ['php5', '/usr/share/asciitosvg/a2s' ]
    # , path, '-t', 'svg', '-o', outpath]
    with open(os.devnull, "w") as fnull:
        p = subprocess.Popen(r, stdout=open(outpath, 'w'),
            stdin=open(path, 'r'), stderr = fnull)
    p.communicate()
    return outpath, 'svg'

def generate_diagram_tikz(path, options):
    ''' generate_diagram_tikz '''
    texfile = path + '.tex'
    pdffile = path + '.pdf'
    psfile = path + '.eps'
    pngfile = path + '.png'
    auxfile = path + '.aux'
    logfile = path + '.log'

    t = open(texfile, 'wb')
    s = open(path, 'r')
    t.write('\\documentclass{article}\n')
    t.write('\\usepackage[pdftex,active,tightpage]{preview}\n')
    if 'border' in options:
        t.write('\\setlength\PreviewBorder{2mm}\n')
    t.write('\\usepackage{tikz}\n')
    t.write('\\begin{document}\n')
    t.write('\\begin{preview}\n')
    t.write(s.read())
    t.write('\\end{preview}\n\\end{document}\n')
    t.flush()
    os.fsync(t.fileno())
    t.close()
    s.close()

    dpis = extract_option(options,'dpis')
    if dpis == None:
        dpis = '150'
    last_cwd = os.getcwd()
    os.chdir('/tmp')
    try:
        subprocess.check_call(['pdflatex', texfile ], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE)
        subprocess.check_call(['pdftops', '-eps', pdffile ])
        subprocess.check_call(['convert', '-density', dpis, psfile, pngfile ])
    except CalledProcessError:
        print 'Error converting to tikz somehow'
        pngfile = None
    for file in [ pdffile, psfile, auxfile, logfile, texfile ]:
        if os.path.exists(file):
            os.remove(file)
    os.chdir(last_cwd)
    return pngfile

def generate_diagram_gnuplot(path, options):
    return None

def detect_first_line(path):
    f = open(path, 'r')
    t = f.readlines()
    for fmt in [ 'ditaa', 'aafigure', 'asciitosvg' ]:
        if t[0].find(fmt) != -1:
            f = tempfile.NamedTemporaryFile(delete=False)
            f.write(string.join(t[1:]))
            n = f.name
            f.close()
            return n, fmt
    return path, None

def detect_diagram_type(path, options):
    # The diagram can be explicitly tagged on
    # it's first line. Otherwise it is deducted
    # from it's content or the default option passed
    # on the command line
    newpath, t = detect_first_line(path)
    if t != None:
        return newpath, t

    types = {
        'tikz' : [ '\\begin{tikzpicture}' ],
        'gnuplot' : ['plot']
    }
    f = open(path, 'r')
    lines = f.readlines()
    for l in lines:
        for k in types.keys():
            for kw in types[k]:
                if l.find(kw) != -1:
                    return path, k
    for fmt in [ 'ditaa', 'aafigure', 'asciitosvg' ]:
        if fmt in options:
            return path, fmt
    return path, 'unknown'

# get_diagram:
# Return the diagram bitmap in a buffer
def get_diagram(options, lines):
    f = tempfile.NamedTemporaryFile(delete=False)
    for line in lines:
        f.write(line + '\n')
    f.close()
    p = f.name
    n, t = detect_diagram_type(p, options)
    # if type == 'unknown':
    if 'ditaa' == t:
        dfile, ext = generate_diagram_ditaa(n, options)
    elif 'aafigure' == t:
        dfile, ext = generate_diagram_aafigure(n, options)
    elif 'asciitosvg' == t:
        dfile, ext = generate_diagram_a2s(n, options)
    elif t == 'tikz':
        dfile = generate_diagram_tikz(n, options)
        ext = 'png'
    elif t == 'gnuplot':
        dfile = generate_diagram_gnuplot(n, options)
    else:
        print 'Specify a default conversor for diagrams! (ditaa/aafigure/a2s)'
        return None, None
    if dfile == None:
        return None
    f = open(dfile, 'r')
    r = f.read()
    if 'svg' in options and 'aafigure' == t:
        # Set width on line four of the outputted svg
        handle = rsvg.Handle(file=dfile)
        lines = r.split('\n')
        lines[4] += (' width="' + str(handle.props.width) +
                     'px" height="' + str(handle.props.height) + 'px"')
        r = string.join(lines, '\n')
    f.close()
    # os.remove(n)
    return r, ext

