# -*- coding: utf-8 -*-

from lib.wikimedia.languages import *

def GetLanguageModule(wikitype, wikilang):
    if wikitype == u'wikipedia':
        if wikilang == u'fr':
            return wikifr.WikiFRTranslator()
    return wikien.WikiEnTranslator()
