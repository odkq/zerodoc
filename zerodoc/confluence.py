#!/usr/bin/env python
"""
    confluence output
    
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
import tempfile
import zerodoc.diagram
import zerodoc.utils

def write_listlines(proc, options, listlines, toc):
    lastlevel = 0
    o = ''
    for uline in listlines:
        s = '*'
        for i in range(uline['level']):
            s += '*'
        if toc:
            s += ' [' + proc.process(uline) + '|#' +\
                zerodoc.utils.get_anchor(uline['string']) + ']\n'
        else:
            s += ' ' + proc.process(uline) + '\n'
        o += s
    return o

def write_sourcelines(proc, options, sourcelines):
    o = '{code:none}\n'
    for sline in sourcelines:
        if 'string' in sline:
            o += proc.process(sline) + '\n'
        else:
            print 'unknown element in sourcelines ' + str(sline) + ' ' + str(sline.keys())
    o += '{code}\n'
    return o

def write_textlines(proc, options, textlines):
    o = '\n'
    for t in textlines:
        o += proc.process(t) + ' '
    o += '\n'
    return o

def write_diagramlines(proc, options, diagramlines):
    dlines = []
    if 'rawdiagrams' in options:
        return write_sourcelines(options, diagramlines)
    for sline in diagramlines:
        if 'string' in sline:
            dlines.append(proc.process(sline))
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
        return '{html}\n<img src="' + n + '" />\n{html}\n'

    duri = str(base64.encodestring(img)).replace("\n", "")
    if not 'svg' in options:
        t = '{html}' + '\n<img alt="sample" src="data:image/png;base64,{0}">\n'.format(duri) + '{html}\n'
    else:
        t = '{html}' + '\n<img alt="sample" src="data:image/svg;base64,{0}">\n'.format(duri) + '{html}\n'
    return t

 
def write_confluence_paragraph(proc, options, para, toc = False):
    o = ''
    if para.has_key('sourcelines'):
        o += write_sourcelines(proc, options, para['sourcelines'])
    elif para.has_key('listlines'):
        o += write_listlines(proc, options, para['listlines'], toc)
    elif para.has_key('textlines'):
        o += write_textlines(proc, options, para['textlines'])
    elif para.has_key('diagramlines'):
        o += write_diagramlines(proc, options, para['diagramlines'])
    return o

def write_confluence_section(proc, options, section):
    o = '\n'
    o += '{anchor:' + zerodoc.utils.get_anchor(section['title']['string']) +'}\n'
    o += 'h' + str(section['level'] + 1) + '. '
    o += section['title']['string'] + '\n'
    for para in section['paragraphs']:
        o += write_confluence_paragraph(proc, options, para)
    return o

def write(doc, options = ['ditaa', 'datauri']):
    '''
    Output the confluence wiki rendering of a doc tree
    '''
    proc = zerodoc.utils.Processor(doc, '[{0}|{1}]')
    o = ''
    # todo put title in post
    o += 'h1. '
    for titleline in doc['header']['title']['textlines']:
        o += proc.process(titleline) + ' '
    o += '\n'
    for para in doc['header']['abstract']['abstract']:
       o += write_confluence_paragraph(proc, options, para)
    # o += '<h2>Table of contents</h2>'
    o += write_confluence_paragraph(proc, options, doc['header']['toc'], toc=True)
    for section in doc['body']['sections']:
        o += write_confluence_section(proc, options, section) 
    return o

