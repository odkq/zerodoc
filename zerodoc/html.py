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
import zerodoc.diagram

def get_header_link(s):
    h = hashlib.new('ripemd160')
    h.update(s.lower())
    return h.hexdigest()[:8]

def process_attributes(doc, line):
    ''' Include attributes and links '''
    s = ''
    a = line['string']
    l = 0
    r = []
    if 'references' in line:
        for reference in line['references']:
            j = reference[1] - l
            s += cgi.escape(a[:j])
            s += '<a href="' + doc['links'][reference[0]] + '">'
            s += reference[0] + '</a>'
            a = a[j:]
            l = reference[1]
        return s
    else:
        return cgi.escape(a)

def write_listlines(doc, options, listlines, toc):
    lastlevel = 0
    o = '<ul>\n'
    for uline in listlines:
        # We can go from 3 to 0, but not to 1 to 3 (an
        # intermediate title is needed)
        # TODO: Do this test in the parser
        d = lastlevel - uline['level']
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
        elif uline['level'] != lastlevel:
            # List indentation error
            # TODO: Notify from the parser?
            o += '<code>error, new listlevel '
            o += str(uline['level'])
            o += ' oldlistlevel ' + str(lastlevel)
            o += '</code>'
        if toc:
            o += '<li>'
            o += '<a href="#' + get_header_link(uline['string']) +'">'
            o += process_attributes(doc, uline)
            o += '</a></li>\n'
        else:
            o += '<li>' + process_attributes(doc, uline) + '</li>\n'
    # Unwind last <ul's>
    for i in range(lastlevel):
        o += '</ul>\n'
    o += '</ul>\n'
    return o

def write_sourcelines(doc, options, sourcelines):
    o = '<pre>\n'
    for sline in sourcelines:
        if 'string' in sline:
            o += process_attributes(doc, sline) + '\n'
        else:
            print 'no string in sourceline? ' + str(sline) + ' ' + str(sline.keys())
    o += '</pre>\n'
    return o

def write_textlines(doc, options, textlines):
    o = '<p>\n'
    for t in textlines:
        o += process_attributes(doc, t) + '\n'
    o += '</p>\n'
    return o

def write_diagramlines(doc, options, diagramlines):
    dlines = []
    if 'rawdiagrams' in options:
        return write_sourcelines(options, diagramlines)
    for sline in diagramlines:
        if 'string' in sline:
            dlines.append(sline['string'])
        else:
            print 'unknown element in sourcelines (diagram)' + str(sline) +\
            ' ' + str(sline.keys())
    img = zerodoc.diagram.get_diagram_ditaa(options, dlines)
    if img == None:
        return ''
    if not 'datauri' in options:
        if not os.path.exists('images'):
            os.mkdir('images')
        f = tempfile.NamedTemporaryFile(delete=False, prefix='zero', dir='images')
        f.write(img)
        n = f.name
        f.close()
        return '<img src="' + n + '" />\n'

    duri = str(base64.encodestring(img)).replace("\n", "")
    if not 'svg' in options:
        t = '<img alt="sample" src="data:image/png;base64,{0}">\n'.format(duri)
    else:
        t = '<img alt="sample" src="data:image/svg;base64,{0}">\n'.format(duri)
    return t

 
def write_html_paragraph(doc, options, para, toc = False):
    o = ''
    if para.has_key('sourcelines'):
        o += write_sourcelines(doc, options, para['sourcelines'])
    elif para.has_key('listlines'):
        o += write_listlines(doc, options, para['listlines'], toc)
    elif para.has_key('textlines'):
        o += write_textlines(doc, options, para['textlines'])
    elif para.has_key('diagramlines'):
        o += write_diagramlines(doc, options, para['diagramlines'])
    return o

def write_html_section(doc, options, section):
    o = ''
    o += '<a name="' + get_header_link(section['title']['string']) + '"></a>'
    o += '<h' + str(section['level'] + 2) 
    o += '>' + section['title']['string'] + '</h'
    o += str(section['level'] + 2) + '>'
    for para in section['paragraphs']:
        o += write_html_paragraph(doc, options, para)
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
            o += process_attributes(doc, titleline) + '\n'
        o += '</title>\n'
        o += '<body>\n'
    o += '<h1>\n'
    for titleline in doc['header']['title']['textlines']:
        o += process_attributes(doc, titleline) + '\n'
    o += '</h1>\n'
    # o += '<h2>Abstract</h2>'
    for para in doc['header']['abstract']['abstract']:
       o += write_html_paragraph(doc, options, para)
    # o += '<h2>Table of contents</h2>'
    o += write_html_paragraph(doc, options, doc['header']['toc'], toc=True)
    for section in doc['body']['sections']:
        o += write_html_section(doc, options, section) 
    if not 'noheaders' in options:
        o += '</body>'
        o += '</html>'
    return o

