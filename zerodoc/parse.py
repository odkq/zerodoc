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
import os
import sys
import ply.lex as lex
import ply.yacc as yacc

# For the time being ...
DEBUG=True

tokens = ( 'SOURCE', 'TEXT', 'TEXTLIST', 'FIRSTLIST', 'FIRSTSOURCE' , 'FIRSTDIAGRAM', 'NEWLINE')

t_TEXT=r'[^-\n\ ][^\n]+'
t_TEXTLIST=r'[\ ]+-[^\n]+'
t_FIRSTLIST=r'-[^\n]+'
t_SOURCE=r'[^-\n][^\n]*'
t_FIRSTSOURCE=r'\ [^-\n\ ][^\n]*'
t_FIRSTDIAGRAM=r'\ [\ ]+[^-\n\ ][^\n]*'

# precedence = (
#    ('left', 'FIRSTTEXTLIST', 'TEXTLIST'),
# )

start = 'document'

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

# Abstract can only have text paragrahps (no lists
# or sourcelines
def p_textparas(p):
    '''textparas : textparas textpara
                | textpara'''
    append_or_create('abstract', p)

def p_paragraphs(p):
    '''paragraphs : paragraphs paragraph
                  | paragraph'''
    append_or_create('paragraphs', p)

def in_toclist(s, d):
    found = None
    level = None
    toc_list = d['header']['toc']
    for e in toc_list['listlines']:
        if e['string'].lower() == s.lower():
            if found != None:
                print 'ERROR: The element ' + e['string'] + 'in TOC is duplicated!'
                sys.exit(1)
            else:
                found = e['string']
                level = e['level']
    return found, level

def p_paragraph(p):
    '''paragraph : textlines NEWLINE
                 | sourcelines NEWLINE
                 | listlines NEWLINE
                 | diagramlines NEWLINE
    '''
    # A paragraph made from listlines can be a list of
    # links
    if 'listlines' in p[1]:
        pass
        # print 'p_paragraph(): [' + str(p[1]['listlines']) + ']'
    p[0] = p[1]

def extract_attributes(x):
    """
    Extract attributes (bold, underline, quote) from text
    >>> extract_attributes("this is *bold*, this is _underline_,\
 this 'quote'")
    {'modified_string': 'this is bold, this is underline, this quote',\
 'bold':[[8,11]], 'underline':[[23,31]], 'quote': [[39,43]]}
    """
    pass

def extract_links(x):
    """Extract links/references from a line. Returns a dictionary
    of {'links':{'keyword': link,...,'keyword': link},
    'references':[[keyword,pos],...,[keyword,pos]],
    'modified_string': s }

    The modified string will not have nor links or references
    on it, and the positions in the array of references
    for are relative to this modified string, not to the
    original one

    >>> extract_links('text line `name`:http://pepe.com continue')
    {'modified_string': 'text line  continue', 'references': [['name', 10]],\
 'links': {'name': 'http://pepe.com'}}

    >>> extract_links('text line `reference1` and `reference2`')
    {'modified_string': 'text line  and ', 'references':\
 [['reference1', 10], ['reference2', 15]], 'links': {}}

    >>> extract_links('text line with no links whatsoever')
    {'modified_string': 'text line with no links whatsoever',\
 'references': [], 'links': {}}

    """
    modified_string = ''
    offset = 0
    references = []
    links = {}
    while True:
        s = x[offset:]
        local_modified_string = ''
        first = s.find('`')
        if first == -1:
            modified_string += s
            break
        second = s[first+1:].find('`')
        if second == -1:
            modified_string += s
            break
        if (second+first+2) >= len(s) or s[second+first+2] != ':':
            # no link afterwards, thus it is a reference
            pos = first + len(modified_string)
            local_modified_string += s[:first]
            # local_modified_string += s[(second+first+3):]
            offset += second+first+2
            ref = s[first+1:second+first+1]
            references.append([ref, pos])
        else:
            third = s[second+first+3:].find(' ')
            if third == -1:
                # eol
                third = len(s)
            pos = first + len(modified_string)
            local_modified_string += s[:first]
            # local_modified_string += s[second+first+third+3:]
            offset += second+first+third+3
            ref = s[first+1:second+first+1]
            link = s[second+first+3:second+first+third+3]
            references.append([ref, pos])
            links[ref] = link
        modified_string += local_modified_string
    return {'links': links, 'references':references,
            'modified_string': modified_string }

def p_textpara(p):
    '''textpara : textlines NEWLINE'''
    p[0] = p[1]

# Lists with only 1 element are not allowed
def p_listlines(p):
    '''listlines : firstlist listline
                 | listlines listline
                 | listlines firstlist
                 | firstlist firstlist'''
    if 'listlines' in p[1]:
        p[0] = p[1] 
        p[0]['listlines'].append(p[2])
    else:
        p[0] = { 'listlines': [p[1], p[2]] }

# Used both for diagrams and source
def insert_source_diagram_vector(p, keyg, key):
    # | firstsource
    if len(p) == 4:
        # create a pseudo p vector
        v = []
        v.append(p[0])
        # reappend the new line
        p[1][keyg][len(p[1][keyg]) - 1][key] += '\n'
        v.append(p[1])
        v.append(p[3])
        append_or_create(keyg, v)
        r = v[0]
    elif len(p) == 2:
        r = { keyg: [p[1]] }
    else:
        if keyg in p[1]:
            r = p[1]
            r[keyg].append(p[2])
        else:
            r = { keyg: [p[1], p[2]] }
    return r
 
def p_sourcelines(p):
    '''sourcelines : sourcelines sourceline
                   | sourcelines firstsource
                   | sourcelines firstdiagram
                   | firstsource sourceline
                   | firstsource 
                   | sourcelines NEWLINE sourceline
                   | sourcelines NEWLINE firstsource'''
    p[0] = insert_source_diagram_vector(p, 'sourcelines', 'string')

def p_diagramlines(p):
    '''diagramlines : diagramlines sourceline
                    | diagramlines firstsource
                    | diagramlines firstdiagram
                    | firstdiagram sourceline
                    | firstdiagram
                    | diagramlines NEWLINE sourceline
                    | diagramlines NEWLINE firstdiagram'''
    p[0] = insert_source_diagram_vector(p, 'diagramlines', 'string')

def p_textlines(p):
    '''textlines : textlines textline
                 | textline'''
    append_or_create('textlines', p)

def p_firstsource(p):
    '''firstsource : FIRSTSOURCE NEWLINE
                   | TEXTLIST NEWLINE'''
    p[0] = { 'string': p[1] } 

def p_firstdiagram(p):
    '''firstdiagram : FIRSTDIAGRAM NEWLINE'''
    p[0] = { 'string': p[1] } 

def p_sourceline(p):
    '''sourceline : SOURCE NEWLINE
                  | TEXTLIST NEWLINE'''
    p[0] = { 'string': p[1]} 

def p_textline(p):
    '''textline : TEXT NEWLINE'''
    p[0] = { 'string': p[1] }

def firstnospace (s):
    n = 0
    for c in s:
        if c == ' ':
            n += 1
        else:
            return n
    return None

def p_listline(p):
    '''listline : TEXTLIST NEWLINE'''
    # The number of spaces determines the indentation
    level = p[1].count(' ', 0, p[1].find('-'))
    p[0] = { 'level': level , 'string': p[1][(level + 2):] }

# the firstlistline is special because it determines wether the block
# is a list paragraph or not
# Todo: allow for various lines
def p_firstlist(p):
    '''firstlist : FIRSTLIST NEWLINE'''
    p[0] = { 'level': 0 , 'string': p[1][2:] }

def p_title(p):
    'title : textlines NEWLINE'
    # Copy directly the textlines as title is
    # prefixed by parent 'header'
    p[0] = p[1]

def p_header(p):
    'header : title textparas listlines NEWLINE'
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
        print "Syntax error at line %d, around '%s'" % (t.lineno, t.value)
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
    lastlevel = -1
    for i in range(nparas):
        para = paras[i]
        if para.has_key('textlines') == False:
            continue
        if len(para['textlines']) != 1:
            continue
        title_candidate = para['textlines'][0]['string']
        toc_string, level = in_toclist(title_candidate, doc)
        if toc_string == None:
            continue
        para['textlines'][0]['string'] = toc_string
        if last == -1:
            last = i
            lastlevel = level
            continue
        lastpara = paras[last]
        section = { 'title': lastpara['textlines'][0], 'level': lastlevel, 'paragraphs' : paras[last+1:i]}
        sections.append(section)
        last = i
        lastlevel = level

    # Last section
    lastpara = paras[last]
    section = { 'title': lastpara['textlines'][0] , 'level': lastlevel, 'paragraphs' : paras[last+1:nparas] }
    sections.append(section)
    
    # From now on paragraphs are organiced into sectors, so delete
    # old paragraphs array
    doc['body']['sections'] = sections
    del doc['body']['paragraphs']

# Append with backslashes
def append(base, new):
    bl = len(base)
    if bl < 2:
        return base + new + '\n'
    if base[(bl-2):] == '\\\n':
        n = firstnospace(new)
        if n == None:
            return base
        return base[:-2] + new[n:] + '\n'
    else:
        return base + new + '\n'

def preprocess(s):
    # line continuations are very tricky to handle inside the grammar,
    # so i took this 'preprocessor' out of the sleeve :>
    o = ''
    e = ''
    n = 0
    inlist = False

    for line in s.split('\n'):
        l = len(line)
        if l == 0:
            if inlist:
                inlist = False
            o = append(o, '')

        if len(line) != 0 and line[0] != ' ':
            l = len(line)
            if len(line) > 72:
                e += 'Line ' + str(n) 
                e += ':In regular paragraphs (no source/diagrams) no'
                e += 'lines bigger than 72 chars are allowed. Use \\'
                return None, e
            else:
                if line[0] == '-':
                    inlist = True
            o = append(o, line)
        if len(line) != 0 and line[0] == ' ':
                if inlist:
                    n = firstnospace(line)
                    if line[n] == '-':
                        o = append(o, line)
                    else:
                        if o[-2:] == '\\\n':
                            o = append(o, line[n:])
                        else:
                            o = append(o[:-1], ' ' + line[n:])
                else:
                    insource = True
                    # No backslash substitution for source
                    # code
                    o += line + '\n'
        n += 1

    # Remove extra \n's at eol
    while o[-1:] == '\n':
        o = o[:-1]
    o += '\n\n'
    return o, None

def extract_links_lines(links, lines):
    ''' Extract links from a group of lines. If the group
        of lines only have links True is returned along with
        the modified array
    '''
    n = []
    links_only = True
    for l in lines:
        r = extract_links(l['string'])
        if r['links'] != {}:
            links.update(r['links'])
        else:
            links_only = False
        if r['references'] != []:
            l['string'] = r['modified_string']
            if l['string'] != '':
                links_only = False
            l['references'] = r['references']
        n.append(l)
    return n, links_only

def extract_links_paragraph(links, para):
    '''
    extract links from listlines and textlines paragraphs only
    (no source/diagrams etc)
    '''
    if para.has_key('listlines'):
        para['listlines'], o = extract_links_lines(links, para['listlines'])
        if o == True:
            del para['listlines']
    elif para.has_key('textlines'):
        para['textlines'], o = extract_links_lines(links, para['textlines'])

def process_links(doc):
    links = {}
    ''' Extract links from source and put them in their tree '''
    for para in doc['header']['abstract']['abstract']:
        extract_links_paragraph(links, para)
    for section in doc['body']['sections']:
        for para in section['paragraphs']:
            extract_links_paragraph(links, para)
    doc['links'] = links

def extract_attributes(doc):
    pass

def parse(s):
    ''' Return the syntax tree for a preloaded string '''
    l = lex.lex(optimize=1, debug=0)
    yacc.yacc(optimize=1, debug=0)
    p, e = preprocess(s)
    if p == None:
        print 'ERROR: ' + e
        return None
    doc = yacc.parse(p)
    # First, adjust 'named' sections from the template
    adjust_sections(doc)
    # Extract links from source and put them in their tree
    process_links(doc)
    # Identify text attributes
    extract_attributes(doc)
    # Parsetab by default is generated on the current directory
    # This is not desirable at all (the directory can be read-only
    # and a program should not write spureous files on its cwd)
    # But, until i figure out a better way to put the parsetab
    # in the installation dir (wich would be the best) just remove
    # it
    if os.path.exists('parsetab.py'):
        os.remove('parsetab.py')
    if os.path.exists('lextab.py'):
        os.remove('lextab.py')
    return doc, None

if __name__ == "__main__":
    import doctest
    doctest.testmod()

