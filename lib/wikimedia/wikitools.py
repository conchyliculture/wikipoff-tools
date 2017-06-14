# -*- coding: utf-8 -*-

from lib.wikimedia.languages import wikien

def GetLanguageModule(wikitype, wikilang):
    if wikitype == u'wikipedia':
        if wikilang == u'fr':
            from lib.wikimedia.languages import wikifr
            return wikifr.WikiFRTranslator()
    return wikien.WikiEnTranslator()
