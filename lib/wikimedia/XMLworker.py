#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import sqlite3
import os
import pprint
pp = pprint.PrettyPrinter(indent=4)
import sys
from lxml import etree
import wikitools
import datetime
import getpass
import tools

class XMLworker(object):

    def GetTranslator(self):
        return wikitools.WikimediaTranslator(self.wikitype, self.infos['lang'])

    def __init__(self, xml_file):
        self.languagedb="lib/wikimedia/languages.sqlite"
        self.xml_file=xml_file
        self.infos=self.get_infos()
        self.wikitype=self.guess_type()
        self.zmq_channel = None

        self.is_allowed_title = self.GetTranslator().get_is_allowed_title_func()

        if not os.path.isfile(self.languagedb):
            print("%s doesn't exists. Please create it."%self.languagedb)
            sys.exit(1)

    def GenerateMessage(self, title, body, msgtype):
        self.zmq_channel.send_json({u'type': msgtype, u'title': title, u'body': body})

    def GenerateRedirect(self, from_, to_):
        self.GenerateMessage(from_, to_, 1)

    def GenerateArticle(self, title, body):
        self.GenerateMessage(title, body, 2)

    def GenerateFinished(self):
        self.GenerateMessage(u'', u'', 0)

    def str(self):
        print("Parsed %s:\n\ttype: %s\n"%(self.xml_file,self.infos['type']))

    def guess_type(self):
        res= re.match(r'wikipedia\.org/wiki',self.infos['base'])
        if res is not None:
            return 'wikipedia'
        return None


    def get_infos(self):
        wiki_infos={}
        infotags = ('sitename', 'dbname', 'base','generator')

        with open(self.xml_file,'r') as xmlfd:
            line=xmlfd.readline()
            res = re.match(r'<mediawiki.*xml:lang="(.+)"',line)
            if res is None:
                print("Input is not a mediawiki xml file? Should start with '<mediawiki' and contain xml:lang=\"somelang\"")
                sys.exit(1)
            else:
                wiki_infos['lang']=res.group(1)


        for event, element in etree.iterparse(self.xml_file):
            tag=element.tag
            index= tag.find(u'}')
            if index>-1:
                tag=tag[index+1:]
            if tag in infotags:
                wiki_infos[tag]=element.text
            elif tag == u'siteinfo':
                # WikiInfo has the required info
                realrnun=True
                element.clear()
                break
            element.clear()
        connlang = sqlite3.connect(self.languagedb)
        curslang = connlang.cursor()
        curslang.execute("SELECT english,local FROM languages WHERE code LIKE ?",(wiki_infos[u'lang'],))
        e,l = curslang.fetchone()
        curslang.close()
        wiki_infos[u'lang-code']=wiki_infos[u'lang']
        wiki_infos[u'lang-local']=l
        wiki_infos[u'lang-english']=e
        wiki_infos[u'type']=wiki_infos[u'sitename']
        wiki_infos[u'author']=getpass.getuser()+u' @ Wikipoff-tools'
        wiki_infos[u'source']= wiki_infos[u'base']
        pp.pprint(wiki_infos) 
        return wiki_infos 

    def process_data(self, zmq_channel):
        self.zmq_channel = zmq_channel
        contenttags = (u'text', u'title', u'id' )
        wikiarticle = {}
        i = 0
        eta_every = 100
        st = datetime.datetime.now() 

        inputsize =  os.path.getsize(self.xml_file)
        stream = open(self.xml_file, 'rb')

        for event, element in etree.iterparse(stream):
            tag = element.tag
            index = tag.find(u'}')
            if index >- 1:
                tag = tag[index+1:]
            if tag in contenttags:
                wikiarticle[tag] = element.text
            elif tag == u'redirect':
                wikiarticle[u'redirect'] = element.get('title')
            elif tag == u'page': # end of article
                redir = wikiarticle.get(u'redirect', None)
                if redir:
                    self.GenerateRedirect(wikiarticle[u'title'], redir)
                    wikiarticle={}
                else:
                    if wikiarticle[u'text'] is None:
                        continue
                    colon=wikiarticle[u'title'].find(u':')
                    if colon>0:
                        if not self.is_allowed_title(wikiarticle[u'title'][0:colon]):
                            continue

                    title = wikiarticle[u'title']
                    body = wikiarticle[u'text']
                    self.GenerateArticle(title, body)
                    wikiarticle={}
                    i+=1
                    if i%eta_every == 0:
                        percent =  (100.0 * stream.tell()) / inputsize
                        delta=((100-percent)*(datetime.datetime.now()-st).total_seconds())/percent
                        status_s= "%.02f%% ETA=%s\r"%(percent, str(datetime.timedelta(seconds=delta)))
                        sys.stdout.write(status_s)
                        sys.stdout.flush()

                element.clear()
        self.GenerateFinished()

    def run(self, zmq_channel):
        try:
            self.process_data(zmq_channel)
        except etree.XMLSyntaxError as e:
            err_msg = u'Whoops, your xml file looks bogus:\n'
            err_msg += e.error_log
            raise Exception(err_msg)

    def set_infos(self):
        self.dest.set_metadata(self.infos)

