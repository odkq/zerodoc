#!/usr/bin/env python
""" 
    Convenient functions that can be used by various renderers
 
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
import hashlib
import cgi

def get_anchor(s):
    '''
    Some standard way to extract and refer to internal hyperlins 
    (called anchors for some markups)
    '''
    h = hashlib.new('ripemd160')
    h.update(s.lower())
    return h.hexdigest()[:8]

class Processor():
    '''
    Include attributes and links in a line with
    a format depending in the output format

    '''
    def __init__(self, doc, format_string, escape_function = None):
        '''
        escape_function is a function that will be called for the
        text parts of the output (cgi.escape for html output for
        example) Pass None to include those verbatim
        '''
        if not escape_function:
            self.escape_function = lambda x: x
        else:
            self.escape_function = escape_function
        self.format_string = format_string
        self.doc = doc

    def process(self, line):
        s = ''
        a = line['string']
        l = 0
        r = []
        if 'references' in line:
            for reference in line['references']:
                j = reference[1] - l
                if j > 0:
                    s += self.escape_function(a[:j])
                try:
                    s += self.format_string.format(reference[0], self.doc['links'][reference[0]])
                except KeyError:
                    return self.escape_function(line['string'])
                a = a[j:]
                l = reference[1]
            if a != '':
                s += self.escape_function(a)
            return s
        else:
            return self.escape_function(a)

