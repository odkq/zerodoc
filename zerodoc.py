#!/usr/bin/env python
""" 
    zerodoc

    Very simple interpreter for a 'plain text format' named zerodoc
    that is parsed into a tree and from there to HTML 2.0/markdown etc

    Built upon the PLY 'lex & yacc for python'. The yacc files and the
    lex regular expressions defining zerodoc can be found interspersed
    in the t_ and p_ functions of this file

"""
import sys
import ply.lex as lex
import ply.yacc as yacc

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

#   if len(p[1][1][1]) == 1:    # With only 1 textline
#        print 'only line ' + p[1][1][1][1]

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
                  | sourceline'''
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
    'listline : TEXTLIST NEWLINE'
    # Remove initial '- '
    p[0] = { 'listline': p[1][2:] }

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
        print "Syntax error at '%s'" % t.value
    else:
        print "Syntax error at EOF"
        # pass

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

if len(sys.argv) != 2:
    print 'Usage: zerodoc <filename>'
    sys.exit(1)

def print_paragraph_html(para):
    if para.has_key('sourcelines'):
        print '<pre>'
        for sline in para['sourcelines']:
            print sline['sourceline']
        print '</pre>'
    elif para.has_key('listlines'):
        print '<ul>'
        for uline in para['listlines']:
            print '<li>' + uline['listline'] + '</li>'
        print '</ul>'
    elif para.has_key('textlines'):
        print '<p>'
        for tline in para['textlines']:
            print tline['textline']
        print '</p>'

def print_section_html(section):
    print '<h2>' + section['title']['textline'] + '</h2>'
    for para in section['paragraphs']:
        print_paragraph_html(para)

def print_html(doc):
    '''
    <html>
    <head>
     <title>Install debian with loop-aes encryption in the root partition</title>
     </head>
     <body>
     <h1>Install debian with loop-aes encryption in the root partition</h1>
    '''
    print '<html>'
    print '<head>'
    print '<title>'
    for titleline in doc['header']['title']['textlines']:
        print titleline['textline']
    print '</title>'
    print '<body>'
    print '<h1>'
    for titleline in doc['header']['title']['textlines']:
        print titleline['textline']
    print '<h2>Abstract</h2>'
    for para in doc['header']['abstract']['paragraphs']:
        print_paragraph_html(para)
    print '<h2>Table of contents</h2>'
    print_paragraph_html(doc['header']['toc'])

    for section in doc['body']['sections']:
        print_section_html(section) 
    print '</body>'
    print '</html>'

l = lex.lex(debug=0)
yacc.yacc(debug=0)
f = open(sys.argv[1], 'r')
document = yacc.parse(f.read())
adjust_sections(document)
#print 'parse tree: '
#print str(document)
#print 'html: '
print_html(document)
