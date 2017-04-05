#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import getpass
import os
import re
import sqlite3
import sys
import lib.wikimedia.wikitools as wikitools
from lxml import etree
if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding(u'utf-8')



class XMLworker(object):
    def __init__(self, xml_file):
        self._languagedb = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), u'languages.sqlite')
        self.xml_file = xml_file
        self.infos = self._GetInfos()
        self.wikitype = self._GuessType()
        self.zmq_channel = None

        if not os.path.isfile(self._languagedb):
            raise Exception(u'{0:s} doesn\'t exists. Please create it.'.format(self._languagedb))

    def GenerateMessage(self, title, body, msgtype):
        self.zmq_channel.send_json({u'type': msgtype, u'title': title, u'body': body})

    def GenerateRedirect(self, from_, to_):
        self.GenerateMessage(from_, to_, 1)

    def GenerateArticle(self, title, body):
        self.GenerateMessage(title, body, 2)

    def GenerateFinished(self):
        self.GenerateMessage(u'', u'', 0)

    def _GuessType(self):
        res = self.infos[u'base'].find(u'wikipedia.org/wiki')
        if res:
            return u'wikipedia'
        return None

    def _GetInfos(self):
        wiki_infos = {}
        infotags = (u'sitename', u'dbname', u'base', u'generator')

        with open(self.xml_file, u'rb') as fd:
            line = fd.readline().decode(u'utf-8')
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
        eta_every = 100
        st = datetime.datetime.now()

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
                            if not wikitools.IsAllowedTitle(
                                header_title, wikitype=self.wikitype,
                                lang=self.infos[u'lang']):
                                continue

                        body = wikiarticle[u'text']
                        self.GenerateArticle(title, body)
                        wikiarticle = {}
                        i += 1
                        if i%eta_every == 0:
                            percent = (100.0 * stream.tell()) / inputsize
                            delta = ((100-percent)*(datetime.datetime.now()-st).total_seconds())/percent
                            status_s = "%.02f%% ETA=%s\r"%(
                                percent, str(datetime.timedelta(seconds=delta)))
                            sys.stdout.write(status_s)
                            sys.stdout.flush()
                    element.clear()

    def run(self, zmq_channel):
        self.zmq_channel = zmq_channel
        try:
            self._ProcessData()
            self.GenerateFinished()
        except etree.XMLSyntaxError as e:
            err_msg = u'Whoops, your xml file looks bogus:\n'
            err_msg += e.error_log
            raise Exception(err_msg)
