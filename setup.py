#!/usr/bin/env python
from distutils.core import setup

classifiers = [
   "Development Status :: 3 - Alpha",
   "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
   "Programming Language :: Python :: 2.6",
   "Topic :: Text Processing :: Markup",
   "Topic :: Text Processing :: Filters",
   "Topic :: Software Development :: Documentation"
   "Environment :: Console",
]

setup(
    name = 'zerodoc',
    version = '0.0.1',
    description = "minimalistic {asciidoc/pod/phpdoc}-alike " +
                  "plaintext to html/markdown/whatever' format" +
                  "with a very simple interpreter and a very" +
                  "simple syntax",
    author = "Pablo Martin",
    author_email = "pablo@odkq.com",
    packages = ['zerodoc'],
    scripts = [
        'scripts/zerodoc'
    ],
    url = "https://github.com/odkq/zerodoc",
    license = "GPL v3",
    # README.0 is written in zerodoc itself
    long_description = open('README.0').read(),
    data_files = [
                ("/usr/share/doc/zerodoc", 
                        [ "README.0"]),
    ],
    classifiers = classifiers
)

