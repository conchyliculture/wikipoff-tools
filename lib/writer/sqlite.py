# encoding: utf-8
import sqlite3
from time import strftime

VERSION = u'2.5'

class OutputSqlite(object):

    REQUIRED_INFO_TAGS = [
        u'lang-code', u'lang-local', u'lang-english',
        u'type', u'source', u'author'
    ]


    def __init__(self, sqlite_file, max_file_size=None):
        self.sqlite_file = sqlite_file
        if sqlite_file:
            self.sqlite_file_tab = sqlite_file.split(u'.')
        self.max_file_size = max_file_size

        self.nb_inserted_articles = 0
        self.file_num = 0

        self.articles_buffer = []
        self.redirects_buffer = []
        self.max_inserts = 1000
        self.max_articles_per_db = None
        self._Open()

    def _Open(self):
        if self.sqlite_file:
            self.sqlite_file = self.sqlite_file
            self.conn = sqlite3.connect(self.sqlite_file)
        else:
            self.conn = sqlite3.connect(u':memory:')

        self.conn.isolation_level = u'EXCLUSIVE'
        self.cursor = self.conn.cursor()
        self.cursor.execute(u'PRAGMA synchronous=NORMAL')
        self.cursor.execute(u'PRAGMA journal_mode=MEMORY')
        self.SetMaxFileSize()

        self.cursor.execute(
            '''CREATE TABLE IF NOT EXISTS articles (_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                    title VARCHAR(255) NOT NULL,
                                                    text BLOB)''')
        self.cursor.execute(
            '''CREATE TABLE IF NOT EXISTS redirects (
                                                    title_from VARCHAR(255) NOT NULL,
                                                    title_to VARCHAR(255))''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS metadata (key TEXT, value TEXT);''')
        self.conn.commit()

    def _GetMetadataValue(self, key):
        val = self.cursor.execute(u'SELECT \'%s\' FROM metadata'% key).fetchone()[0]
        return val

    def GetMetadata(self):
        res = {}
        for k, v in self.cursor.execute(u'SELECT * from metadata'):
            res[k] = v
        return res

    def SetMetadata(self, infos):
        self._CheckRequiredInfos(infos)

        self._SetLang(infos[u'lang-code'], infos[u'lang-local'], infos[u'lang-english'])
        self._SetGenDate(strftime(u'%Y-%m-%d %H:%M:%S'))
        self._SetVersion(VERSION)
        self._SetSource(infos[u'source'])
        self._SetAuthor(infos[u'author'])
        self._SetType(infos[u'type'])

    def _CheckRequiredInfos(self, infos):
        for key in self.REQUIRED_INFO_TAGS:
            res = infos.get(key, None)
            if not res:
                raise Exception(u'We lack required infos : {0:s}'.format(key))

    def SetMaxFileSize(self):
        # Rough estimation is ~2k of final DB size per article
        if self.max_file_size:
            self.max_articles_per_db = (self.max_file_size*1024)/2

    def _SetLang(self, lang_code, lang_local, lang_english):
        self.cursor.execute(
            u'INSERT OR REPLACE INTO metadata VALUES (\'lang-code\', ?)', (lang_code,))
        self.cursor.execute(
            u'INSERT OR REPLACE INTO metadata VALUES (\'lang-local\', ?)', (lang_local,))
        self.cursor.execute(
            u'INSERT OR REPLACE INTO metadata VALUES (\'lang-english\', ?)', (lang_english,))

    def _SetGenDate(self, sdate):
        self.cursor.execute(
            u'INSERT OR REPLACE INTO metadata VALUES (\'date\', ?)', (sdate,))

    def _SetVersion(self, version):
        self.cursor.execute(
            u'INSERT OR REPLACE INTO metadata VALUES (\'version\', ?)', (version,))

    def _SetType(self, stype):
        self.cursor.execute(u'INSERT OR REPLACE INTO metadata VALUES (\'type\', ?)', (stype,))

    def _SetAuthor(self, stype):
        self.cursor.execute(u'INSERT OR REPLACE INTO metadata VALUES (\'author\', ?)', (stype,))

    def _SetSource(self, stype):
        self.cursor.execute(u'INSERT OR REPLACE INTO metadata VALUES (\'source\', ?)', (stype,))

    def AddRedirect(self, source, dest):
        self.redirects_buffer.append((source, dest))
        if len(self.redirects_buffer) == self.max_inserts:
            self.cursor.executemany(u'INSERT INTO redirects VALUES (?, ?)', self.redirects_buffer)
            self.redirects_buffer = []

    def AddArticle(self, title, text):
        self.articles_buffer.append((title, text))
        self.nb_inserted_articles += 1
        if len(self.articles_buffer) == self.max_inserts:
            self.cursor.executemany(
                u'INSERT INTO articles VALUES (NULL, ?, ?)', self.articles_buffer)
            self.articles_buffer = []
        if self.max_articles_per_db:
            if self.nb_inserted_articles >= self.max_articles_per_db:
                self.file_num +=1
                self.Close()
                self.sqlite_file = u'.'.join(self.sqlite_file_tab[:-1]) + u'-{0:d}'.format(self.file_num)+ u'.sqlite'
                print(u'DB full, making a new one: %s'%self.sqlite_file)
                self._Open()
                self.nb_inserted_articles = 0

    def _AllCommit(self):
        if len(self.articles_buffer) > 0:
            self.cursor.executemany(
                u'INSERT INTO articles VALUES (NULL, ?, ?)', self.articles_buffer)
        if len(self.redirects_buffer) > 0:
            self.cursor.executemany(
                u'INSERT INTO redirects VALUES (?, ?)', self.redirects_buffer)
        self.articles_buffer = []
        self.redirects_buffer = []
        self.conn.commit()

    def Close(self):
        self._AllCommit()
        self.cursor.execute(u'CREATE INDEX tidx1 ON articles(title)')
        self.cursor.execute(u'CREATE INDEX tidx2 ON redirects(title_from)')
        self.cursor.execute(u'CREATE VIRTUAL TABLE searchTitles USING fts3(_id, title);')
        print(u'Building FTS table')
        self.cursor.execute(
            u'INSERT INTO searchTitles(_id, title) SELECT _id, title FROM articles;')
        self.conn.commit()
        print(u'Cleaning up')
        self.cursor.execute(u'VACUUM')
        self.cursor.close()
        self.conn.close()
