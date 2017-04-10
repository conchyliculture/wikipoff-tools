#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import getpass
import os
import re
import sqlite3
import lib.wikimedia.wikitools as wikitools
from lxml import etree


class XMLworker(object):
    def __init__(self, xml_file):
        self._languagedb = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), u'languages.sqlite')
        self.xml_file = xml_file
        self.db_metadata = self._GetInfos()
        self.wikitype = self._GuessType()
        self.out_queue = None
        self.counter = 0

        self.percent = None

        if not os.path.isfile(self._languagedb):
            raise Exception(u'{0:s} doesn\'t exists. Please create it.'.format(self._languagedb))

        self.language_helper = wikitools.GetLanguageModule(self.wikitype, self.db_metadata[u'lang'])

    def GenerateMessage(self, title, body, msgtype):
        self.out_queue.put({u'type': msgtype, u'title': title, u'body': body})

    def GenerateRedirect(self, from_, to_):
        self.counter += 1
        self.GenerateMessage(from_, to_, 1)

    def GenerateArticle(self, title, body):
        self.counter += 1
        self.GenerateMessage(title, body, 2)

    def GenerateFinished(self, expected):
        self.GenerateMessage(expected, u'', 0)

    def _GuessType(self):
        res = self.db_metadata[u'base'].find(u'wikipedia.org/wiki')
        if res:
            return u'wikipedia'
        return None

    def _GetInfos(self):
        wiki_infos = {}
        infotags = (u'sitename', u'dbname', u'base', u'generator')

        with open(self.xml_file, u'rb') as fd:
            line = fd.readline().decode('utf-8')
            res = re.match(r'<mediawiki.*xml:lang="(.+)"', line)
            if not res:
                raise Exception(
                    u'Input is not a mediawiki xml file? Should start with '
                    u'\'<mediawiki\' and contain xml:lang="somelang"')
            else:
                wiki_infos[u'lang'] = res.group(1)

            for _, element in etree.iterparse(fd, encoding=u'utf-8'):
                tag = element.tag
                index = tag.find(u'}')
                if index > -1:
                    tag = tag[index+1:]
                if tag in infotags:
                    wiki_infos[tag] = element.text
                elif tag == u'siteinfo':
                    # WikiInfo has the required info
                    element.clear()
                    break
                element.clear()

        connlang = sqlite3.connect(self._languagedb)
        curslang = connlang.cursor()
        curslang.execute(
            u'SELECT english, local FROM languages WHERE code LIKE ?',
            (wiki_infos[u'lang'],))
        e, l = curslang.fetchone()
        curslang.close()
        wiki_infos[u'lang-code'] = wiki_infos[u'lang']
        wiki_infos[u'lang-local'] = l
        wiki_infos[u'lang-english'] = e
        wiki_infos[u'type'] = wiki_infos[u'sitename']
        wiki_infos[u'author'] = getpass.getuser() + u' @ Wikipoff-tools'
        wiki_infos[u'source'] = wiki_infos[u'base']
        return wiki_infos

    def _ProcessData(self):
        contenttags = (u'text', u'title', u'id')
        wikiarticle = {}
        i = 0
        eta_every = 300

        inputsize = os.path.getsize(self.xml_file)

        with open(self.xml_file, 'rb') as stream:
            for _, element in etree.iterparse(stream, encoding=u'utf-8'):
                tag = element.tag
                index = tag.find(u'}')
                if index > -1:
                    tag = tag[index+1:]
                if tag in contenttags:
                    wikiarticle[tag] = element.text
                elif tag == u'redirect':
                    wikiarticle[u'redirect'] = element.get(u'title')
                elif tag == u'page': # end of article
                    redir = wikiarticle.get(u'redirect', None)
                    if redir:
                        self.GenerateRedirect(wikiarticle[u'title'], redir)
                        wikiarticle = {}
                    else:
                        if wikiarticle[u'text'] is None:
                            continue
                        title = wikiarticle[u'title']
                        colon = title.find(u':')
                        if colon > 0:
                            header_title = title[0:colon]
                            if not self.language_helper.IsAllowedTitle(header_title):
                                continue

                        body = wikiarticle[u'text']
                        self.GenerateArticle(title, body)
                        wikiarticle = {}
                        i += 1
                        if (i % eta_every) == 0:
                            self.percent.value = (100.0 * stream.tell()) / inputsize
                    element.clear()

    def run(self, out_queue, status):
        self.out_queue = out_queue
        self.percent = status
        try:
            self._ProcessData()
            self.GenerateFinished(self.counter)
        except etree.XMLSyntaxError as e:
            err_msg = u'Whoops, your xml file looks bogus:\n'
            err_msg += e.error_log
            raise Exception(err_msg)
