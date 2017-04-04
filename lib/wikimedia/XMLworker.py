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

class XMLworker():
    def __init__(self,xml_file,dest,convert=True):
        self.languagedb="lib/wikimedia/languages.sqlite"
        self.xml_file=xml_file
        self.dest=dest
#        if isinstance(xml_file, file):
#            self.infos=dest.get_metadata()
#            self.wikitype=self.infos["type"]
#        else:
        self.infos=self.get_infos()
        self.wikitype=self.guess_type()

        self.translator=wikitools.WikimediaTranslator(self.wikitype,self.infos['lang'])
        self.is_allowed_title = self.translator.get_is_allowed_title_func()

        self.convert=convert

        self.set_infos()

        if not os.path.isfile(self.languagedb):
            print("%s doesn't exists. Please create it."%self.languagedb)
            sys.exit(1)

    def set_convert(self,c=True):
        self.convert=c

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

    def process_data(self):
        contenttags = (u'text', u'title', u'id' )
        wikiarticle={}
        i=0
        eta_every = 100
        st = datetime.datetime.now() 

#        if not type(self.xml_file)==file:
        inputsize =  os.path.getsize(self.xml_file)
        stream = open(self.xml_file, 'rb')
#        else:
#        stream=self.xml_file

        for event, element in etree.iterparse(stream):
            tag = element.tag
            index = tag.find(u'}')
            if index >- 1:
                tag = tag[index+1:]
            if tag in contenttags:
                wikiarticle[tag] = element.text
            elif tag == u'redirect':
                wikiarticle[u'redirect']=True
            elif tag == u'page': # end of article
#                print wikiarticle['title']
                redir = wikiarticle.get(u'redirect', None)
                if redir:
                    self.dest.insert_redirect(wikiarticle[u'title'],wikiarticle[u'redirect'])
                    wikiarticle={}
                else:
                    if wikiarticle[u'text'] is None:
                        continue
                    colon=wikiarticle[u'title'].find(u':')
                    if colon>0:
                        if not self.is_allowed_title(wikiarticle[u'title'][0:colon]):
                            continue
                    wikitools.WikiDocumentSQL(self.dest, wikiarticle[u'title'], wikiarticle[u'text'],self.translator,convert=self.convert)
                    wikiarticle={}
                    i+=1
                    if i%eta_every == 0:
                        percent =  (100.0 * stream.tell()) / inputsize
                        delta=((100-percent)*(datetime.datetime.now()-st).total_seconds())/percent
                        status_s= "%.02f%% ETA=%s\r"%(percent, str(datetime.timedelta(seconds=delta)))
                        sys.stdout.write(status_s)
                        sys.stdout.flush()

                element.clear()

    def run(self):
        try:
            self.process_data()
        except etree.XMLSyntaxError as e:
            print("Whoops, your xml file looks bogus:\n")
            print(e.error_log)

    def close(self):
        self.dest.close()
        pass


    def set_infos(self):

        self.dest.set_metadata(self.infos)

