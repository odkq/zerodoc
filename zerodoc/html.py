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
import string
import tempfile
import subprocess
import zerodoc.diagram
import zerodoc.utils

def write_listlines(proc, options, listlines, toc):
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
            o += '<a href="#' + zerodoc.utils.get_anchor(uline['string']) +'">'
            o += proc.process(uline)
            o += '</a></li>\n'
        else:
            o += '<li>' 
            o += proc.process(uline)
            o += '</li>\n'
    # Unwind last <ul's>
    for i in range(lastlevel):
        o += '</ul>\n'
    o += '</ul>\n'
    return o

def write_sourcelines(proc, options, sourcelines):
    if 'pygments' in options:
        o = '<pre>\n'
        for sline in sourcelines:
            if 'string' in sline:
                o += proc.process(sline) + '\n'
            else:
                print 'no string in sourceline? ' + str(sline) + ' ' + str(sline.keys())
        o += '</pre>\n'
    else:
        f = tempfile.NamedTemporaryFile(delete=False,
            prefix='zero', dir='/tmp')
        for sline in sourcelines:
            if 'string' in sline:
                # Do not process line
                f.write(sline['string'] + '\n')
                # f.write(proc.process(sline) + '\n')
        n = f.name
        f.close()
        output = n + '.html'
        subprocess.call(['pygmentize', '-f', 'html', '-l', 'c', '-o',
            output, n])
        o = open(output).read()
        os.remove(n)
        os.remove(output)
    return o

def write_deflist(proc, options, deflist):
    o = '<dl>'
    o += '<dt>'
    for t in deflist['term']['textlines']:
        o += proc.process(t) + '\n'
    o += '<dd>'
    for t in deflist['definition']['textlines']:
        o += proc.process(t) + '\n'
    o += '</dl>'
    return o

def write_textlines(proc, options, textlines):
    o = '<p>\n'
    for t in textlines:
        o += proc.process(t) + '\n'
    o += '</p>\n'
    return o

def write_diagramlines(proc, options, diagramlines):
    dlines = []
    if 'rawdiagrams' in options:
        return write_sourcelines(options, diagramlines)
    for sline in diagramlines:
        if 'string' in sline:
            dlines.append(sline['string'])
        else:
            print 'unknown element in sourcelines (diagram)' + str(sline) +\
            ' ' + str(sline.keys())
    img, ext = zerodoc.diagram.get_diagram(options, dlines)
    if img == None:
        return ''
    if not 'datauri' in options:
        if not os.path.exists('images'):
            os.mkdir('images')
        f = tempfile.NamedTemporaryFile(suffix='.' + ext, delete=False, prefix='zero', dir='images')
        f.write(img)
        n = f.name
        f.close()
        return '<img src="' + n + '" />\n'

    if ext == 'png':
        # Embed png using 'datauri' old trick
        duri = str(base64.encodestring(img)).replace("\n", "")
        t = '<img alt="sample" src="data:image/' + ext + ';base64,{0}">\n'.format(duri)
    else:
        # Embed svg directly in the html file
        # remove first 4 lines (<xml> and doctype) and set witdth and height
        # attributes that aafigure does not set)
        lines = img.split('\n')[4:]
        t = string.join(lines,'\n')
        
    return t

 
def write_html_paragraph(proc, options, para, toc = False):
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

def write_html_section(proc, options, section):
    o = ''
    o += '<a name="' + zerodoc.utils.get_anchor(section['title']['string']) + '"></a>'
    o += '<h' + str(section['level'] + 2) 
    o += '>' + section['title']['string'] + '</h'
    o += str(section['level'] + 2) + '>'
    for para in section['paragraphs']:
        o += write_html_paragraph(proc, options, para)
    return o

def write(doc, options = ['ditaa', 'datauri']):
    '''
    Output the HTML 2.0 rendering of a doc tree
    '''
    proc = zerodoc.utils.Processor(doc, '<a href="{1}">{0}</a>', cgi.escape)
    o = ''
    if not 'noheaders' in options:
        if not 'html5' in options:
            # i know, i know..
            o += '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0 Strict//EN">\n'
        else:
            o += '<!DOCTYPE html>\n'
        o += '<html>\n'
        o += '<head>\n'
        if not 'html5' in options:
            o += '<meta http-equiv="Content-Type" content="text/html;charset=iso-8859-1" >'
        else:
            o += '<meta charset="utf-8">\n'
            css = None
            for option in options:
                if option[:3] == 'css':
                    css = option.split(':')[1]
            if css:
                if 'datauri' in options:
                    o += '<style media="screen" type="text/css">'
                    o += open(css).read()
                    o += '</style>'
                else:
                    o += '<link rel="stylesheet" href="' + css + '">\n'
        o += '<title>\n'
        for titleline in doc['header']['title']['textlines']:
            o += proc.process(titleline) + '\n'
        o += '</title>\n'
        o += '<body>\n'
    o += '<h1>\n'
    for titleline in doc['header']['title']['textlines']:
        o += proc.process(titleline) + '\n'
    o += '</h1>\n'
    # o += '<h2>Abstract</h2>'
    for para in doc['header']['abstract']['abstract']:
        if para['textlines'][0]['string'] == 'Table of contents':
            continue
        o += write_html_paragraph(proc, options, para)
    o += '<h3>Table of contents</h3>'
    o += write_html_paragraph(proc, options, doc['header']['toc'], toc=True)
    for section in doc['body']['sections']:
        o += write_html_section(proc, options, section) 
    if not 'noheaders' in options:
        o += '</body>'
        o += '</html>'
    return o

