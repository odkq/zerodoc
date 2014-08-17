#!/usr/bin/env python
""" 
    zerodoc reStructuredText (http://docutils.sourceforge.net/rst.html)
    output
    
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
import string
import tempfile
import subprocess
import zerodoc.diagram
import zerodoc.utils
import rsvg

def write_listlines(proc, options, listlines, toc):
    lastlevel = 0
    # o = '<ul>\n'
    o = '\n'
    for uline in listlines:
        # We can go from 3 to 0, but not to 1 to 3 (an
        # intermediate title is needed)
        # TODO: Do this test in the parser
        d = lastlevel - uline['level']
        if d == -1:
            # Certain formats make list delimiters depend on level, - * +
            # and so on. It's not the case of HTML
            lastlevel += 1
        elif d > 0:
            # Unwind <ul's>
            for i in range(d):
                # o += '</ul>\n'
                lastlevel -= 1
        elif uline['level'] != lastlevel:
            # List indentation error
            # TODO: Notify from the parser?
            o += '<code>error, new listlevel '
            o += str(uline['level'])
            o += ' oldlistlevel ' + str(lastlevel)
            o += '</code>'
        if toc:
            o += ' ' * (uline['level'] * 2) + '- '
            # o += '<a href="#' + zerodoc.utils.get_anchor(uline['string']) +'">'
            o += proc.process(uline) + '\n\n'
            # o += '</a>\n\n'
        else:
            o += ' ' * (uline['level'] * 2) + '- '
            o += proc.process(uline) + '\n\n'
    # Unwind last <ul's>
    # for i in range(lastlevel):
    #   o += '</ul>\n'
    #o += '</ul>\n'
    return o

def write_sourcelines(proc, options, sourcelines):
    o = '::\n\n'
    for sline in sourcelines:
        if 'string' in sline:
            o += proc.process(sline) + '\n'
        else:
            print 'no string in sourceline? ' + str(sline) + ' ' + str(sline.keys())
    return o

def write_deflist(proc, options, deflist):
    o = '\n'        # Indented lines need a blank line before in rest??
    for t in deflist['term']['textlines']:
        o += proc.process(t) + '\n'
    for t in deflist['definition']['textlines']:
        # There is no need to overindent, as restructuredText indents text
        # automatically
        o += proc.process(t) + '\n'
    return o

def write_textlines(proc, options, textlines):
    o = '\n'
    for t in textlines:
        o += proc.process(t) + '\n'
    return o

def write_diagramlines(proc, options, diagramlines):
    return '(some diagram here)'

 
def write_rst_paragraph(proc, options, para, toc = False):
    o = ''
    if para.has_key('sourcelines'):
        o += write_sourcelines(proc, options, para['sourcelines'])
    elif para.has_key('listlines'):
        o += write_listlines(proc, options, para['listlines'], toc)
    elif para.has_key('textlines'):
        o += write_textlines(proc, options, para['textlines'])
    elif para.has_key('diagramlines'):
        o += write_diagramlines(proc, options, para['diagramlines'])
    elif para.has_key('deflist'):
        o += write_deflist(proc, options, para['deflist'])
    return o

def write_rst_section(proc, options, section):
    o = ''
    # o += '<a name="' + zerodoc.utils.get_anchor(section['title']['string']) + '"></a>'
    # if section['level'] == 
    o += section['title']['string'] + '\n'
    subtitles = ['=', '-', '~']
    if section['level'] > 2:
        subtitle = '~'
    else:
        subtitle = subtitles[section['level']]
    o += subtitle * len(section['title']['string']) + '\n'
    for para in section['paragraphs']:
        o += write_rst_paragraph(proc, options, para)
    o += '\n\n'
    return o

def write(doc, options = ['ditaa', 'datauri']):
    '''
    Output the reStructuredText rendering of a doc tree
    '''
    proc = zerodoc.utils.Processor(doc, '`{0} <{1}>`_')
    o = ''
    # o += '<h1>\n'
    rst_title = ''
    for titleline in doc['header']['title']['textlines']:
        rst_title += proc.process(titleline) # + '\n'
    o += '=' * len(rst_title) + '\n'
    o += rst_title + '\n'
    o += '=' * len(rst_title) + '\n'
    # o += '</h1>\n'
    # o += '<h2>Abstract</h2>'
    for para in doc['header']['abstract']['abstract']:
       o += write_rst_paragraph(proc, options, para)
    # o += '<h2>Table of contents</h2>'
    o += write_rst_paragraph(proc, options, doc['header']['toc'], toc=True)
    for section in doc['body']['sections']:
        o += write_rst_section(proc, options, section) 
    return o

