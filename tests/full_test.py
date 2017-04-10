#!/usr/bin/python
# coding: utf-8

from __future__ import unicode_literals

import os
import sys
sys.path.append("..")
sys.path.append("../lib/python{0:d}.{1:d}/site-packages/".format(sys.version_info.major,  sys.version_info.minor))
from lib.writer.sqlite import OutputSqlite
import sqlite3
import subprocess
from time import sleep
import unittest
from WikiExtractor import WikiExtractor


class ConvertWiki(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(ConvertWiki, cls).setUpClass()
        cls.xml_filename = u'furwiki-latest-pages-articles.xml'
        cls.xml_dump_path = os.path.join(u'test_data', cls.xml_filename)
        cls.zipped_dump_path = os.path.join(u'test_data', cls.xml_filename+u'.gz')
        if not os.path.exists(cls.xml_dump_path):
            print(u'Decompressing {0:s}'.format(cls.zipped_dump_path))
            subprocess.check_call([u'gzip', u'-d', cls.zipped_dump_path])

        cls.sqlite_temp_path = os.path.join(u'test_data', u'test_sqlite')
        if os.path.exists(cls.sqlite_temp_path):
            os.remove(cls.sqlite_temp_path)

    @classmethod
    def tearDownClass(cls):
        super(ConvertWiki, cls).tearDownClass()

        if not os.path.exists(cls.zipped_dump_path):
            subprocess.check_call([u'gzip', cls.xml_dump_path])

        if os.path.exists(cls.sqlite_temp_path):
            os.remove(cls.sqlite_temp_path)

    def test_SQLstuff(self):
        main = WikiExtractor(self.xml_dump_path, self.sqlite_temp_path)
        print(u'Converting to DB... Please wait')
        main.run()
        sql = main.output
        self.assertIsInstance(sql, OutputSqlite)

        conn = sqlite3.connect(self.sqlite_temp_path)
        cursor = conn.cursor()

        cursor.execute(u'SELECT count(*) from articles')
        articles_count = cursor.fetchone()

        cursor.execute(u'SELECT count(*) from articles')
        articles_count = cursor.fetchone()
        self.assertEqual(4420, articles_count[0])

        cursor.execute(u'SELECT count(*) from redirects')
        redirects_count = cursor.fetchone()
        self.assertEqual(668, redirects_count[0])

if __name__ == '__main__':
    unittest.main()
