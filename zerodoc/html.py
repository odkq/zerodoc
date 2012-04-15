#!/usr/bin/env python
""" 
    zerodoc html 2.0 output
    
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
import cgi
import hashlib

def get_header_link(s):
    h = hashlib.new('ripemd160')
    h.update(s.lower())
    return h.hexdigest()[:8]

def write_html_paragraph(para, toc = False):
    o = ''
    if para.has_key('sourcelines'):
        o += '<pre>\n'
        for sline in para['sourcelines']:
            if 'sourceline' in sline:
                o += sline['sourceline'] + '\n'
            elif 'textline' in sline:
                print 'mixed sourceline and textline in sourcelines'
                o += sline['textline'] + '\n'
            else:
                print 'unknown element in sourcelines ' + str(sline) + ' ' + str(sline.keys())
        o += '</pre>\n'
    elif para.has_key('listlines'):
        o += '<ul>'
        for uline in para['listlines']:
            if toc:
                o += '<li>'
                o += '<a href="#' + get_header_link(uline['listline']) +'">'
                o += uline['listline']
                o += '</a></li>\n'
            else:
                o += '<li>' + uline['listline'] + '</li>\n'
        o += '</ul>\n'
    elif para.has_key('textlines'):
        o += '<p>\n'
        for t in para['textlines']:
            o += t['textline'] + '\n'
        o += '</p>\n'
    return o

def write_html_section(section):
    o = ''
    o += '<a name="' + get_header_link(section['title']['textline']) + '"></a>'
    o += '<h2>' + section['title']['textline'] + '</h2>'
    for para in section['paragraphs']:
        o += write_html_paragraph(para)
    return o

def write(doc):
    '''
    Output the html 2.0 "representation" of a doc tree
    '''
    o = ''
    o += '<html>\n'
    o += '<head>\n'
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
    for para in doc['header']['abstract']['paragraphs']:
        o += write_html_paragraph(para)
    # o += '<h2>Table of contents</h2>'
    o += write_html_paragraph(doc['header']['toc'], toc=True)

    for section in doc['body']['sections']:
        o += write_html_section(section) 
    o += '</body>'
    o += '</html>'
    return o
