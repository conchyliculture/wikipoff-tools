#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# =============================================================================
#  Version: Lorraine (21 Jan 2014
#   Heavily Hacked by renzo for the need of https://github.com/conchyliculture/wikipoff
#
#  Version: 2.6 (Oct 14, 2013)
#  Author: Giuseppe Attardi (attardi@di.unipi.it), University of Pisa
#	   Antonio Fuschetto (fuschett@di.unipi.it), University of Pisa
#
#  Contributors:
#	Leonardo Souza (lsouza@amtera.com.br)
#	Juan Manuel Caicedo (juan@cavorite.com)
#	Humberto Pereira (begini@gmail.com)
#	Siegfried-A. Gevatter (siegfried@gevatter.com)
#	Pedro Assis (pedroh2306@gmail.com)
#
# =============================================================================
#  Copyright (c) 2009. Giuseppe Attardi (attardi@di.unipi.it).
# =============================================================================
#  This file is part of Tanl.
#
#  Tanl is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License, version 3,
#  as published by the Free Software Foundation.
#
#  Tanl is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
# =============================================================================

import sys
sys.path.append("./lib")
sys.path.append("./lib/python2.7/site-packages/pylzma-0.4.4-py2.7-linux-x86_64.egg/")
import gc
import getopt
import urllib
import struct
from cStringIO import StringIO
import bz2
import os.path
import base64
import sqlite3
import pylzma
from time import strftime
from wikimedia import XMLworker
#=========================================================================
#
# MediaWiki Markup Grammar
 
# Template = "{{" [ "msg:" | "msgnw:" ] PageName { "|" [ ParameterName "=" AnyText | AnyText ] } "}}" ;
# Extension = "<" ? extension ? ">" AnyText "</" ? extension ? ">" ;
# NoWiki = "<nowiki />" | "<nowiki>" ( InlineText | BlockText ) "</nowiki>" ;
# Parameter = "{{{" ParameterName { Parameter } [ "|" { AnyText | Parameter } ] "}}}" ;
# Comment = "<!--" InlineText "-->" | "<!--" BlockText "//-->" ;
#
# ParameterName = ? uppercase, lowercase, numbers, no spaces, some special chars ? ;
#
#=========================================================================== 

# Program version
version = '2.5'
dbversion = "0.0.0.1"

##### Main function ###########################################################

inputsize = 0

class OutputSqlite:

    REQUIRED_INFO_TAGS=['lang-code','lang-local','lang-english',
                        'type', 'source','author'
            ]

    def __init__(self, sqlite_file,max_page_count=None):
        global dbversion
        self.sqlite_file=sqlite_file
        self.conn = sqlite3.connect(sqlite_file)
        self.conn.isolation_level="EXCLUSIVE"
        self.curs = self.conn.cursor()
        self.curs.execute("PRAGMA synchronous=NORMAL")
        self.curs.execute("PRAGMA journal_mode=MEMORY")
        if (max_page_count!=None):
            self.set_max_page_count(max_page_count)

        self.curs.execute('''CREATE TABLE IF NOT EXISTS articles (_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                                                  title VARCHAR(255) NOT NULL,
                                                                  text BLOB)''')
        self.curs.execute('''CREATE TABLE IF NOT EXISTS redirects (
                                                                  title_from VARCHAR(255) NOT NULL,
                                                                  title_to VARCHAR(255))''')
        self.curs.execute('''CREATE TABLE IF NOT EXISTS metadata (key TEXT, value TEXT);''')
        self.conn.commit()
        self.curr_values=[]
        self.max_inserts=100

    def set_metadata(self,infos):
        self.check_required_infos(infos)

        self.set_lang(infos['lang-code'],infos['lang-local'],infos['lang-english'])
        self.set_gen_date(strftime("%Y-%m-%d %H:%M:%S"))
        self.set_version(version)
        self.set_source(infos['source'])
        self.set_author(infos['author'])
        self.set_type(infos['type'])


    def check_required_infos(self,infos):
        for key in self.REQUIRED_INFO_TAGS:
            if (not infos.has_key(key)):
                print "We lack required infos : %s"%key
                sys.exit(1)


    def set_max_page_count(self,max_page_count):
        self.curs.execute("PRAGMA max_page_count=%d"%max_page_count)
    def insert_redirect(self,from_,to_):
        self.curs.execute("INSERT INTO redirects VALUES (?,?)",(from_,to_))

    def set_lang(self,lang_code,lang_local,lang_english):
        self.curs.execute("INSERT OR REPLACE INTO metadata VALUES ('lang-code',?)",(lang_code,))
        self.curs.execute("INSERT OR REPLACE INTO metadata VALUES ('lang-local',?)",(lang_local,))
        self.curs.execute("INSERT OR REPLACE INTO metadata VALUES ('lang-english',?)",(lang_english,))

    def set_langlocal(self,lang):
        self.curs.execute("INSERT OR REPLACE INTO metadata VALUES ('lang-local',?)",(lang,))

    def set_langenglish(self,lang):
        self.curs.execute("INSERT OR REPLACE INTO metadata VALUES ('lang-english',?)",(lang,))

    def set_gen_date(self,sdate):
        self.curs.execute("INSERT OR REPLACE INTO metadata VALUES ('date',?)",(sdate,))

    def set_version(self,version):
        self.curs.execute("INSERT OR REPLACE INTO metadata VALUES ('version',?)",(version,))

    def set_type(self,stype):
        self.curs.execute("INSERT OR REPLACE INTO metadata VALUES ('type',?)",(stype,))

    def set_author(self,stype):
        self.curs.execute("INSERT OR REPLACE INTO metadata VALUES ('author',?)",(stype,))

    def set_source(self,stype):
        self.curs.execute("INSERT OR REPLACE INTO metadata VALUES ('source',?)",(stype,))

    def reserve(self,size):
        pass

    def write(self,title,text,raw=False):
        if (len(self.curr_values)==self.max_inserts):
            self.curs.executemany("INSERT INTO articles VALUES (NULL,?,?)",self.curr_values)
            self.conn.commit()
            self.curr_values=[]
        if raw:
            self.curr_values.append((title,text))
        else:
            c=pylzma.compressfile(StringIO(text),dictionary=23)
            result=c.read(5)
            result+=struct.pack('<Q', len(text))
            self.curr_values.append((title,buffer(result+c.read())))
            
    def close(self):
        if (len(self.curr_values)>0):
            self.curs.executemany("INSERT INTO articles VALUES (NULL,?,?)",self.curr_values)
        self.conn.commit()
        print("Building indexes")
        self.curs.execute("CREATE INDEX tidx1 ON articles(title)")
        self.curs.execute("CREATE INDEX tidx2 ON redirects(title_from)")
        self.curs.execute("CREATE VIRTUAL TABLE searchTitles USING fts3(_id, title);")
        print("Building FTS table")
        self.curs.execute("INSERT INTO searchTitles(_id,title) SELECT _id,title FROM articles;")
        self.conn.commit()
        print("Cleaning up")
        self.curs.execute("VACUUM")
        self.curs.close()
        self.conn.close()




def show_usage():
    print """Usage: python WikiExtractor.py  [options] -x wikipedia.xml
Converts a wikipedia XML dump file into sqlite databases to be used in WikipOff

Options:
        -x, --xml       Input xml dump
        -d, --db        Output database file (default : 'wiki.sqlite') 
        -h, --help      Print this help
        -t, --type      Wikimedia type (default: 'wikipedia')
"""

def main():
    global prefix,inputsize
    script_name = os.path.basename(sys.argv[0])

    try:
        long_opts = ['help', "db=", "xml=",'type=']
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'hx:d:t:', long_opts)
    except getopt.GetoptError:
        show_usage()
        sys.exit(1)

    compress = False
    output_file=""

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            show_usage()
            sys.exit()
        elif opt in ('-d', '--db'):
            output_file = arg
        elif opt in ('-x','--xml'):
            input_file = arg

    if not 'input_file' in locals():
        print("Please give me a wiki xml dump with -x or --xml")
        sys.exit()

    if output_file is None or output_file=="":
        print "I need a filename for the destination sqlite file"
        sys.exit(1)

    if os.path.isfile(output_file):
        print("%s already exists. Won't overwrite it."%output_file)
        sys.exit(1)

    dest = OutputSqlite(output_file)

    worker = XMLworker.XMLworker(input_file,dest)  

    print("Converting xml dump %s to database %s. This may take eons..."%(input_file,output_file))

    worker.run()
    worker.close()

if __name__ == '__main__':
    main()
