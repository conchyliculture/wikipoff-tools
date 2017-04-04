#!/usr/bin/python

import sqlite3
from time import strftime

version = u'2.5'
dbversion = u'0.0.0.1'

class OutputSqlite:

    REQUIRED_INFO_TAGS = [
        'lang-code','lang-local','lang-english',
        'type', 'source','author'
    ]

    def __init__(self, sqlite_file, max_page_count=None):
        self.sqlite_file=sqlite_file
        self.conn = sqlite3.connect(sqlite_file)
        self.conn.isolation_level="EXCLUSIVE"
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA synchronous=NORMAL")
        self.cursor.execute("PRAGMA journal_mode=MEMORY")
        if (max_page_count!=None):
            self.set_max_page_count(max_page_count)

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS articles (_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                                                  title VARCHAR(255) NOT NULL,
                                                                  text BLOB)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS redirects (
                                                                  title_from VARCHAR(255) NOT NULL,
                                                                  title_to VARCHAR(255))''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS metadata (key TEXT, value TEXT);''')
        self.conn.commit()
        self.articles_buffer = []
        self.redirects_buffer = []
        self.max_inserts = 1000


    def set_metadata(self, infos):
        self.check_required_infos(infos)

        self.set_lang(infos['lang-code'],infos['lang-local'],infos['lang-english'])
        self.set_gen_date(strftime("%Y-%m-%d %H:%M:%S"))
        self.set_version(version)
        self.set_source(infos['source'])
        self.set_author(infos['author'])
        self.set_type(infos['type'])


    def check_required_infos(self,infos):
        for key in self.REQUIRED_INFO_TAGS:
            res = infos.get(key, None)
            if not res:
                print("We lack required infos : %s"%key)
                sys.exit(1)


    def set_max_page_count(self,max_page_count):
        self.cursor.execute(u'PRAGMA max_page_count=%d'%max_page_count)

    def AddRedirect(self, source, dest):
        if (len(self.redirects_buffer) == self.max_inserts):
            self.cursor.executemany(u'INSERT INTO redirects VALUES (?, ?)', self.redirects_buffer)
            self.redirects_buffer = []
        self.redirects_buffer.append((source, dest))

    def set_lang(self,lang_code,lang_local,lang_english):
        self.cursor.execute("INSERT OR REPLACE INTO metadata VALUES ('lang-code',?)",(lang_code,))
        self.cursor.execute("INSERT OR REPLACE INTO metadata VALUES ('lang-local',?)",(lang_local,))
        self.cursor.execute("INSERT OR REPLACE INTO metadata VALUES ('lang-english',?)",(lang_english,))

    def set_langlocal(self,lang):
        self.cursor.execute("INSERT OR REPLACE INTO metadata VALUES ('lang-local',?)",(lang,))

    def set_langenglish(self,lang):
        self.cursor.execute("INSERT OR REPLACE INTO metadata VALUES ('lang-english',?)",(lang,))

    def set_gen_date(self,sdate):
        self.cursor.execute("INSERT OR REPLACE INTO metadata VALUES ('date',?)",(sdate,))

    def set_version(self,version):
        self.cursor.execute("INSERT OR REPLACE INTO metadata VALUES ('version',?)",(version,))

    def set_type(self,stype):
        self.cursor.execute("INSERT OR REPLACE INTO metadata VALUES ('type',?)",(stype,))

    def set_author(self,stype):
        self.cursor.execute("INSERT OR REPLACE INTO metadata VALUES ('author',?)",(stype,))

    def set_source(self,stype):
        self.cursor.execute("INSERT OR REPLACE INTO metadata VALUES ('source',?)",(stype,))

    def reserve(self,size):
        pass

    def AddArticle(self, title, text):
        if (len(self.articles_buffer) == self.max_inserts):
            self.cursor.executemany(u'INSERT INTO articles VALUES (NULL,?,?)', self.articles_buffer)
            self.articles_buffer = []
        self.articles_buffer.append((title,text))
            
    def Close(self):
        if (len(self.articles_buffer) > 0):
            self.cursor.executemany("INSERT INTO articles VALUES (NULL,?,?)",self.articles_buffer)
        if (len(self.redirects_buffer) > 0):
            self.cursor.executemany("INSERT INTO redirects VALUES (?,?)",self.redirects_buffer)
        self.cursor.execute("CREATE INDEX tidx1 ON articles(title)")
        self.cursor.execute("CREATE INDEX tidx2 ON redirects(title_from)")
        self.cursor.execute("CREATE VIRTUAL TABLE searchTitles USING fts3(_id, title);")
        print("Building FTS table")
        self.cursor.execute("INSERT INTO searchTitles(_id,title) SELECT _id,title FROM articles;")
        self.conn.commit()
        print("Cleaning up")
        self.cursor.execute("VACUUM")
        self.cursor.close()
        self.conn.close()


