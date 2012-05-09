#!/usr/bin/env python
""" 
    zerodoc html 2.0 (http://tools.ietf.org/rfc/rfc1866.txt) output
    
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
import base64
import hashlib
import tempfile
import subprocess

def get_header_link(s):
    h = hashlib.new('ripemd160')
    h.update(s.lower())
    return h.hexdigest()[:8]

def write_listlines(options, listlines, toc):
    lastlevel = 0
    o = '<ul>\n'
    for uline in listlines:
        # We can go from 3 to 0, but not to 1 to 3 (an
        # intermediate title is needed)
        # TODO: Do this test in the parser
        d = lastlevel - uline['listline']['level']
        if d == -1:
            # Certain formats make list delimiters depend on level, - * +
            # and so on. It's not the case of HTML
            o += '<ul>\n'
            lastlevel += 1
        elif d > 0:
            # Unwind <ul's>
            for i in range(d):
                o += '</ul>\n'
                lastlevel -= 1
        elif uline['listline']['level'] != lastlevel:
            # List indentation error
            # TODO: Notify from the parser?
            o += '<code>error, new listlevel '
            o += str(uline['listline']['level'])
            o += ' oldlistlevel ' + str(lastlevel)
            o += '</code>'
        if toc:
            o += '<li>'
            o += '<a href="#' + get_header_link(uline['listline']['string']) +'">'
            o += uline['listline']['string']
            o += '</a></li>\n'
        else:
            o += '<li>' + uline['listline']['string'] + '</li>\n'
    # Unwind last <ul's>
    for i in range(lastlevel):
        o += '</ul>\n'
    o += '</ul>\n'
    return o

def write_sourcelines(options, sourcelines):
    o = '<pre>\n'
    for sline in sourcelines:
        if 'sourceline' in sline:
            o += sline['sourceline'] + '\n'
        elif 'textline' in sline:
            print 'mixed sourceline and textline in sourcelines'
            o += sline['textline'] + '\n'
        else:
            print 'unknown element in sourcelines ' + str(sline) + ' ' + str(sline.keys())
    o += '</pre>\n'
    return o

def write_textlines(options, textlines):
    o = '<p>\n'
    for t in textlines:
        o += t['textline'] + '\n'
    o += '</p>\n'
    return o

def generate_diagram_image(path):
    r = ['java', '-jar', '/opt/ditaa0_9.jar', path ]
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
 
def write_html_paragraph(options, para, toc = False):
    o = ''
    if para.has_key('sourcelines'):
        o += write_sourcelines(options, para['sourcelines'])
    elif para.has_key('listlines'):
        o += write_listlines(options, para['listlines'], toc)
    elif para.has_key('textlines'):
        o += write_textlines(options, para['textlines'])
    elif para.has_key('diagramlines'):
        o += write_diagramlines(options, para['diagramlines'])
    return o

def write_html_section(options, section):
    o = ''
    o += '<a name="' + get_header_link(section['title']['textline']) + '"></a>'
    o += '<h' + str(section['level'] + 2) 
    o += '>' + section['title']['textline'] + '</h'
    o += str(section['level'] + 2) + '>'
    for para in section['paragraphs']:
        o += write_html_paragraph(options, para)
    return o

def write(doc, options = ['ditaa', 'datauri']):
    '''
    Output the HTML 2.0 rendering of a doc tree
    '''
    o = ''
    if not 'noheaders' in options:
        o += '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0 Strict//EN">\n'
        o += '<html>\n'
        o += '<head>\n'
        o += '<meta http-equiv="Content-Type" content="text/html;charset=iso-8859-1" >'
        o += '<title>\n'
        for titleline in doc['header']['title']['textlines']:
            o += titleline['textline'] + '\n'
        o += '</title>\n'
        o += '<body>\n'
    o += '<h1>\n'
    for titleline in doc['header']['title']['textlines']:
        o += titleline['textline'] + '\n'
    o += '</h1>\n'
    # o += '<h2>Abstract</h2>'
    for para in doc['header']['abstract']['abstract']:
       o += write_html_paragraph(options, para)
    # o += '<h2>Table of contents</h2>'
    o += write_html_paragraph(options, doc['header']['toc'], toc=True)
    for section in doc['body']['sections']:
        o += write_html_section(options, section) 
    if not 'noheaders' in options:
        o += '</body>'
        o += '</html>'
    return o

