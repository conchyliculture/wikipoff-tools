#!/usr/bin/python
# coding: utf-8

from __future__ import unicode_literals

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), u'..'))
sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        u'..', u'lib', u'python{0:d}.{1:d}'.format(
            sys.version_info.major, sys.version_info.minor),
        u'site-packages'))
import sqlite3
import subprocess
import unittest

from lib.writer.sqlite import OutputSqlite
from WikiConverter import WikiDoStuff


class ConvertWiki(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(ConvertWiki, cls).setUpClass()
        cls.xml_filename = u'furwiki-latest-pages-articles.xml'
        cls.xml_dump_path = os.path.join(
                os.path.dirname(__file__), u'test_data', cls.xml_filename)
        cls.zipped_dump_path = os.path.join(
                os.path.dirname(__file__), u'test_data', cls.xml_filename + u'.gz')
        if not os.path.exists(cls.xml_dump_path):
            print(u'Decompressing {0:s}'.format(cls.zipped_dump_path))
            subprocess.check_call([u'gzip', u'-d', cls.zipped_dump_path])


    @classmethod
    def tearDownClass(cls):
        super(ConvertWiki, cls).tearDownClass()

        if not os.path.exists(cls.zipped_dump_path):
            subprocess.check_call([u'gzip', cls.xml_dump_path])


    def test_SQLstuff(self):
        sqlite_temp_path = os.path.join(
                os.path.dirname(__file__), u'test_data', u'test.sqlite')
        if os.path.exists(sqlite_temp_path):
            os.remove(sqlite_temp_path)
        main = WikiDoStuff(self.xml_dump_path, sqlite_temp_path)
        print(u'Converting to DB... Please wait')
        main.run()
        sql = main.output
        self.assertIsInstance(sql, OutputSqlite)

        conn = sqlite3.connect(sqlite_temp_path)
        conn.text_factory = bytes
        cursor = conn.cursor()

        cursor.execute(u'SELECT count(*) from articles')
        articles_count = cursor.fetchone()

        cursor.execute(u'SELECT count(*) from articles')
        articles_count = cursor.fetchone()
        self.assertEqual(4240, articles_count[0])

        cursor.execute(u'SELECT count(*) from redirects')
        redirects_count = cursor.fetchone()
        self.assertEqual(668, redirects_count[0])

        search_title = u'Lenghe furlane'
        cursor.execute(u'SELECT * from articles WHERE title = ? LIMIT 1', (search_title,))
        _, article_title, article_body = cursor.fetchone()
        self.assertEqual(search_title, article_title.decode(u'utf-8'))
        self.assertEqual(5519, len(article_body))

        if os.path.exists(sqlite_temp_path):
            os.remove(sqlite_temp_path)

    def test_SQLstuff_split(self):
        sqlite_temp_path = os.path.join(
                os.path.dirname(__file__), u'test_data', u'test.sqlite')
        sqlite_temp_path_1 = os.path.join(
                os.path.dirname(__file__), u'test_data', u'test-1.sqlite')
        if os.path.exists(sqlite_temp_path_1):
            os.remove(sqlite_temp_path_1)
        main = WikiDoStuff(self.xml_dump_path, sqlite_temp_path, max_file_size=5)
        print(u'Converting to DB... Please wait')
        main.run()
        sql = main.output
        self.assertIsInstance(sql, OutputSqlite)

        conn = sqlite3.connect(sqlite_temp_path)

        conn.text_factory = bytes
        cursor = conn.cursor()

        cursor.execute(u'SELECT count(*) from articles')
        articles_count = cursor.fetchone()

        cursor.execute(u'SELECT count(*) from articles')
        articles_count = cursor.fetchone()
        self.assertEqual(2560, articles_count[0])

        cursor.execute(u'SELECT count(*) from redirects')
        redirects_count = cursor.fetchone()
        self.assertEqual(283, redirects_count[0])

        search_title = u'Lenghe furlane'
        cursor.execute(u'SELECT * from articles WHERE title = ? LIMIT 1', (search_title,))
        _, article_title, article_body = cursor.fetchone()
        self.assertEqual(search_title, article_title.decode(u'utf-8'))
        self.assertEqual(5519, len(article_body))

        conn = sqlite3.connect(u'test_data/test-1.sqlite')
        conn.text_factory = bytes
        cursor = conn.cursor()

        cursor.execute(u'SELECT count(*) from articles')
        articles_count = cursor.fetchone()

        cursor.execute(u'SELECT count(*) from articles')
        articles_count = cursor.fetchone()
        self.assertEqual(1680, articles_count[0])

        cursor.execute(u'SELECT count(*) from redirects')
        redirects_count = cursor.fetchone()
        self.assertEqual(385, redirects_count[0])

        if os.path.exists(sqlite_temp_path):
            os.remove(sqlite_temp_path)
        if os.path.exists(sqlite_temp_path_1):
            os.remove(sqlite_temp_path_1)

if __name__ == '__main__':
    unittest.main()
