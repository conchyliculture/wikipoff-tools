#!/Usr/bin/python
# encoding: utf-8

from __future__ import unicode_literals

class WikiEnTranslator(object):

    @staticmethod
    def IsAllowedTitle(title):
        return title not in [
            u'Blog', u'Category', u'Category talk', u'Discussion', u'File', u'Figure',
            u'File talk', u'Forum', u'Forum talk', u'Help', u'Help talk', u'MediaWiki',
            u'MediaWiki talk', u'Talk', u'Template', u'Template talk', u'User', u'User blog',
            u'User talk', u'User blog comment']

    def Translate(self, text):
        return text
