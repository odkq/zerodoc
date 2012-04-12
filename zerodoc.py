#!/usr/bin/env python
""" 
    zerodoc

    Very simple interpreter for a 'plain text format' named zerodoc
    that is parsed into a tree and from there to HTML 2.0/markdown etc

    Built upon the PLY 'lex & yacc for python'. The yacc files and the
    lex regular expressions defining zerodoc can be found interspersed
    in the t_ and p_ functions of this file

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
import sys
import json
import hashlib
import optparse
import ply.lex as lex
import ply.yacc as yacc

# For the time being ...
DEBUG=True

tokens = ( 'TEXT', 'TEXTLIST', 'SPACE', 'NEWLINE')

t_TEXT=r'[^-\n\ ][^\n]+'
t_SPACE=r'\ '
t_TEXTLIST=r'-[^\n]+'

start = 'document'

# Wheter we are in header, when list items are part of the
# TOC, or not
in_header = True

# Link to the base of the tree after parsing (yacc.yacc()
def t_NEWLINE(t):
    r'\n'
    t.lexer.lineno += len(t.value)
    return t

def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    return False


def test(lexer,data):
    lexer.input(data)
    while 1:
         tok = lexer.token()
         if not tok: break
         print tok

def append_or_create(name, p):
    ''' When working on a rule that 'groups' several
        elements together, generate an array if it is
        the first element or append to the existing one'''
    if len(p) == 3:     # elements: elements element
        p[0] = p[1]
        p[0][name].append(p[2])
    else:               # elements: element (first occurrence)
        p[0] = { name: [] }
        p[0][name].append(p[1])
    return p[0]

def p_paragraphs(p):
    '''paragraphs : paragraphs paragraph
                  | paragraph'''
    append_or_create('paragraphs', p)

def in_toclist(s, d):
    found = False
    toc_list = d['header']['toc']
    for e in toc_list['listlines']:
        if e['listline'].lower() == s.lower():
            if found == True:
                print 'ERROR: The element ' + e['listline'] + 'in TOC is duplicated!'
                sys.exit(1)
            else:
                found = True
    return found

def p_paragraph(p):
    'paragraph : textlines NEWLINE'
    p[0] = p[1]

def p_listlines(p):
    '''listlines : listlines listline
                 | listline'''
    append_or_create('listlines', p)

def p_sourcelines(p):
    '''sourcelines : sourcelines sourceline
                   | sourceline
                   | sourcelines NEWLINE sourceline'''
    if len(p) == 3:
        # create a pseudo p vector
        v = []
        v.append(p[0])
        v.append(p[1])
        v.append(p[2])
        append_or_create('sourcelines', v)
        p[0] = v[0]
    else:
        append_or_create('sourcelines', p)

def p_textlines(p):
    '''textlines : textlines textline
                 | textline
                 | listlines
                 | sourcelines'''

    # This is not a regular append_or_create
    # Because this rule can receive listlines
    # or sourcelines, in wich case it just replaces
    # the array with it
    if len(p) == 3:
        p[0] = p[1]         # copy textlines dict
        p[0]['textlines'].append(p[2])   # Append new textline
    else:
        if p[1].has_key('listlines') or p[1].has_key('sourcelines'):
            # Just copy the array of listlines/sourcelines
            p[0] = p[1]
        else:      # Create a new 'textlines' array
            p[0] = {'textlines': []}
            p[0]['textlines'].append(p[1])   # Append text or list

def p_sourceline(p):
    'sourceline : SPACE TEXT NEWLINE'
    p[0] = { 'sourceline': p[2] } 

def p_textline(p):
    '''textline : TEXT NEWLINE'''
    p[0] = { 'textline': p[1] }

def p_listline(p):
    '''listline : TEXTLIST NEWLINE
                | listline SPACE SPACE TEXT NEWLINE'''
    if len(p) == 3:
        # First line
        p[0] = { 'listline': p[1][2:] }
    else:
        # Append existing listline string interposing a space
        p[0] = { 'listline': p[1]['listline'] + ' ' + p[4] } 

def p_title(p):
    'title : textlines NEWLINE'
    # Copy directly the textlines as title is
    # prefixed by parent 'header'
    p[0] = p[1]

def p_header(p):
    'header : title paragraphs listlines NEWLINE'
    # The real rule (the resulting tree will have):
    # title paragraphs toc NEWLINE
    p[0] = { 'title': p[1], 'abstract': p[2], 'toc': p[3] }
    in_header = False

def p_body(p):
    'body : paragraphs'
    # In the tree there will not be a 'paragraphs'
    # branch, but several 'section' branches. As titles
    # have no special markup and have to be matched against
    # toc titles, no grammar can define them (better said,
    # i do not know how)
    p[0] = p[1]

def p_document(p):
    '''document : header body'''
    p[0] = { 'header': p[1], 'body': p[2]}
    document = p[0]
    # print str(p[0])

def p_error(t):
    if t:
        print "Syntax error at line %d, character '%s'" % (t.lineno, t.value)
    else:
        print "Syntax error at EOF"
    sys.exit(0)

def adjust_sections(doc):
    ''' Walk the parsed tree looking for paragraphs that are title
        sections and reorganize the tree with sections '''
    sections = []
    paras = doc['body']['paragraphs']
    nparas = len(paras)
    last = -1
    for i in range(nparas):
        para = paras[i]
        if para.has_key('textlines') == False:
            continue
        if len(para['textlines']) != 1:
            continue
        title_candidate = para['textlines'][0]['textline']
        if in_toclist(title_candidate, doc) == False:
            continue
        if last == -1:
            last = i
            continue
        lastpara = paras[last]
        section = { 'title': lastpara['textlines'][0] , 'paragraphs' : paras[last+1:i]}
        sections.append(section)
        last = i 

    # Last section
    lastpara = paras[last]
    section = { 'title': lastpara['textlines'][0] , 'paragraphs' : paras[last+1:nparas] }
    sections.append(section)
    
    # From now on paragraphs are organiced into sectors, so delete
    # old paragraphs array
    doc['body']['sections'] = sections
    del doc['body']['paragraphs']


def get_header_link(s):
    h = hashlib.new('ripemd160')
    h.update(s.lower())
    return h.hexdigest()[:8]

def write_html_paragraph(para, toc = False):
    o = ''
    if para.has_key('sourcelines'):
        o += '<pre>\n'
        for sline in para['sourcelines']:
            o += sline['sourceline'] + '\n'
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

def write_html(doc):
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

def parse_file(path):
    ''' Return the syntax tree after parsing a file, or None, 'error string'
        if an error parsing it is encountered ''' 
    f = open(path, 'r')
    s = f.read()
    if DEBUG:
        print '--- input: '
        print(s)
    return parse_string(s)

def parse_string(s):
    ''' Return the syntax tree for a preloaded string '''
    l = lex.lex(debug=0)
    yacc.yacc(debug=0)
    doc = yacc.parse(s)
    adjust_sections(doc)
    return doc, None

def parse_file_into(input, output):
    ''' Transform the zerodoc input and write the result into another
        file ''' 
    f = open(output, 'w')
    d, errstr = parse_file(input)
    if DEBUG:
        print '--- python tree: '
        print str(d)
        print '--- JSON output: '
        print json.dumps(d, indent=2)
        print '--- HTML output: '
        print write_html(d)
    f.write(write_html(d))
    f.close()
    return True

if __name__=="__main__":
    if len(sys.argv) != 3:
        print 'Usage: zerodoc <filename> <output>'
        sys.exit(1)
    parse_file_into(sys.argv[1], sys.argv[2])

