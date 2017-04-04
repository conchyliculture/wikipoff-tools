#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path.append("..")

import unittest
from lib.writer.sqlite import OutputSqlite
from lib.wikimedia.lang import wikifr

import locale
locale.setlocale(locale.LC_ALL, u'fr_FR.utf-8')

class TestSQLWriter(unittest.TestCase):

    def testCheckRequiredInfos(self):
        o = OutputSqlite(None)
        with self.assertRaises(Exception):
            o._CheckRequiredInfos({})

        good_tags = {
            u'lang-code': u'lol',
            u'lang-local': u'lil',
            u'lang-english': u'lolu',
            u'type': u'lola',
            u'source': u'loly',
            u'author': u'lolll'
        }
        o.SetMetadata(good_tags)


    def test_AddRedirect(self):
        o = OutputSqlite(None)
        test_redirect = (u'From', u'To')
        o.AddRedirect(*test_redirect)
        o._AllCommit()

        o.cursor.execute(u'SELECT * FROM redirects')
        self.assertEqual(test_redirect,  o.cursor.fetchone())

    def test_AddArticle(self):
        o = OutputSqlite(None)
        test_article = (u'This title &  à_è>Ýü', u"{{Japonais|'''Lolicon'''|ロリータ・コンプレックス|''rorīta konpurekkusu''}}, ou {{japonais|'''Rorikon'''|ロリコン}}")
        o.AddArticle(*test_article)
        o._AllCommit()

        o.cursor.execute(u'SELECT * FROM articles')
        self.assertEqual((1, test_article[0], test_article[1]),  o.cursor.fetchone())

    def test_Close(self):
        o = OutputSqlite(None)
        test_article = (u'This title &  à_è>Ýü', u"{{Japonais|'''Lolicon'''|ロリータ・コンプレックス|''rorīta konpurekkusu''}}, ou {{japonais|'''Rorikon'''|ロリコン}}")
        o.AddArticle(*test_article)
        test_redirect = (u'From', u'To')
        o.AddRedirect(*test_redirect)
        o._AllCommit()
        o.Close()

class TestWIkiFr(unittest.TestCase):
    sfrt = wikifr.SaveFRTemplates()

    def testLang(self):
        tests = [
            ["lolilol ''{{lang|la|domus Dei}}''","lolilol ''domus Dei''"],
            ["''{{lang-en|Irish Republican Army}}, IRA'' ; ''{{lang-ga|Óglaigh na hÉireann}}'') est le nom porté","''Irish Republican Army, IRA'' ; ''Óglaigh na hÉireann'') est le nom porté"],
            ["{{lang|ko|입니다.}}","입니다."],
            ["Ainsi, le {{lang|en|''[[Quicksort]]''}} (ou tri rapide)","Ainsi, le ''[[Quicksort]]'' (ou tri rapide)"],
            [" ''{{lang|hy|Hayastan}}'', {{lang|hy|Հայաստան}} et ''{{lang|hy|Hayastani Hanrapetut’yun}}'', {{lang|hy|Հայաստանի Հանրապետություն}}"," ''Hayastan'', Հայաստան et ''Hayastani Hanrapetut’yun'', Հայաստանի Հանրապետություն"],
            ["{{langue|ja|酸度}} || １.４（{{langue|ja|芳醇}}","酸度 || １.４（芳醇"],
            ["{{langue|thaï|กรุงเทพฯ}}","กรุงเทพฯ"],
            ["{{Lang|ar|texte=''Jabal ad Dukhan''}}","''Jabal ad Dukhan''"],
            ["{{lang|arc-Hebr|dir=rtl|texte=ארמית}} {{lang|arc-Latn|texte=''Arāmît''}},}}","ארמית ''Arāmît'',}}"],
            ["ce qui augmente le risque de {{lang|en|''[[Mémoire virtuelle#Swapping|swapping]]''}})","ce qui augmente le risque de ''[[Mémoire virtuelle#Swapping|swapping]]'')"]
        ]

        for t in tests:
            self.assertEqual(self.sfrt.save(t[0]), t[1])

    def testDateShort(self):
        tests=[
            [u'{{1er janvier}}', u'1<sup>er</sup> janvier'],
            [u'{{1er février}}', u'1<sup>er</sup> février'],
            [u'Le {{1er mars}}, le débarquement, prévu ', u'Le 1<sup>er</sup> mars, le débarquement, prévu '],
            [u'{{1er avril}}', u'1<sup>er</sup> avril'],
            [u'{{1er mai}}', u'1<sup>er</sup> mai'],
            [u'{{1er juin}}', u'1<sup>er</sup> juin'],
            [u'{{1er juillet}}', u'1<sup>er</sup> juillet'],
            [u'{{1er août}}', u'1<sup>er</sup> août'],
            [u'{{1er septembre}}', u'1<sup>er</sup> septembre'],
            [u'{{1er octobre}}', u'1<sup>er</sup> octobre'],
            [u'{{1er novembre}}', u'1<sup>er</sup> novembre'],
            [u'{{1er décembre}}', u'1<sup>er</sup> décembre'],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.save(t[0]),t[1])

    def testDate(self):
        tests = [
            [u'{{date|10|août|1425}}', u'10 août 1425'],
            [u'{{Date|10|août|1989}} - {{Date|28|février|1990}}', u'10 août 1989 - 28 février 1990'],
            [u'{{date|6|février|1896|en France}}', u'6 février 1896'],
            [u'{{Date|1er|janvier|537}}', u'1er janvier 537'],
            [u'{{Date||Octobre|1845|en sport}}', u'Octobre 1845'],
            [u'{{Date|1|octobre|2005|dans les chemins de fer}}', u'1er octobre 2005'],
            [u'les {{Date|25|mars}} et {{Date|8|avril|1990}}', u'les 25 mars et 8 avril 1990'],
            [u'Jean-François Bergier, né à [[Lausanne]], le {{date de naissance|5|décembre|1931}} et mort le {{date de décès|29|octobre|2009}}&lt;ref name=&quot;swissinfo&quot;/&gt;, est un [[historien]] [[suisse]].', u'Jean-François Bergier, né à [[Lausanne]], le 5 décembre 1931 et mort le 29 octobre 2009&lt;ref name=&quot;swissinfo&quot;/&gt;, est un [[historien]] [[suisse]].'],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.save(t[0]), t[1])

    def testSimpleSiecle(self):
        tests=[
                [u"{{Ier siècle}}, {{IIe siècle}}, ... {{XXe siècle}}, ...",u"Ier siècle, IIe siècle, ... XXe siècle, ..."],
                [u"{{Ier siècle av. J.-C.}}, {{IIe siècle av. J.-C.}}, ...",u"Ier siècle av. J.-C., IIe siècle av. J.-C., ..."],
                [u"{{Ier millénaire}}, {{IIe millénaire}}, ...",u"Ier millénaire, IIe millénaire, ..."],
                [u"{{Ier millénaire av. J.-C.}}, {{IIe millénaire av. J.-C.}}, ...",u"Ier millénaire av. J.-C., IIe millénaire av. J.-C., ..."],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.save(t[0]), t[1])

    def testGSiecles(self):
        tests=[
                [u"{{sp|VII|e|ou|VIII|e|}}",u"VIIe ou VIIIe siècle"],
                [u"{{sp-|VII|e|ou|VIII|e|}}",u"VIIe ou VIIIe siècle"],
                [u"{{-sp|IX|e|-|VII|e|s}}",u"IXe - VIIe siècles av. J.-C."],
                [u"{{-sp-|IX|e|-|VII|e|s}}",u"IXe - VIIe siècles av. J.-C."],
                [u"au {{sp-|XII|e|et au|XVI|e}}",u"au XIIe et au XVIe siècle"],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.save(t[0]), t[1])

    def testTemperature(self):
        tests=[
            [u'température supérieure à {{tmp|10|°C}}.', u'température supérieure à 10°C.'],
            [u'Il se décompose de façon explosive aux alentours de {{tmp|95|°C}}.', u'Il se décompose de façon explosive aux alentours de 95°C.'],
            [u'Entre 40 et {{tmp|70|°C}}', u'Entre 40 et 70°C'],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.save(t[0]), t[1])

    def testSiecle(self):
        tests=[
                ["{{s|III|e}}",     u"IIIe siècle"],
                ["{{-s|III|e}}",    u"IIIe siècle av. J.-C. "],
                ["{{s-|III|e}}",    u"IIIe siècle"],
                ["{{-s-|III|e}}",   u"IIIe siècle av. J.-C. "],
                ["{{s2|III|e|IX|e}}",   u"IIIe et IXe siècles"],
                ["{{-s2|III|e|IX|e}}",  u"IIIe et IXe siècles av. J.-C. "],
                ["{{s2-|III|e|IX|e}}",  u"IIIe et IXe siècles"],
                ["{{-s2-|III|e|IX|e}}",     u"IIIe et IXe siècles av. J.-C. "],
                [u"{{s-|XIX|e|}}", u"XIXe siècle"],

        ]
        for t in tests:
            self.assertEqual(self.sfrt.save(t[0]), t[1])

    def testUnit(self):
        tests = [
            [u'{{Unité|1234567}}', u'1 234 567'],
            [u'{{Unité|1234567.89}}', u'1 234 567.89'],
            [u'{{Unité|1234567,89}}', u'1 234 567.89'],
            [u'{{Unité|1.23456789|e=15}}', u'1.23456789×10<sup>15</sup>'],
            [u'{{Unité|10000|km}}', u'10 000 km'],
            [u'{{nombre|8|[[bit]]s}}', u'8 [[bit]]s'],
            [u'{{nombre|1000|[[yen]]s}}', u'1 000 [[yen]]s'],
            [u'{{nombre|9192631770|périodes}}', u'9 192 631 770 périodes'],
            [u'{{nombre|3620|hab. par km|2}}', u'3 620 hab. par km<sup>2</sup>'],
            [u'{{Unité|10000|km/h}}', u'10 000 km/h'],

            [u'{{Unité|10000|km|2}}', u'10 000 km<sup>2</sup>'],
            [u'{{Unité|10000|m|3}}', u'10 000 m<sup>3</sup>'],
            [u'{{Unité|10000|km||h|-1}}', u'10 000 km⋅h<sup>-1</sup>'],
            [u'{{Unité|10000|J|2|K|3|s|-1}}', u'10 000 J<sup>2</sup>⋅K<sup>3</sup>⋅s<sup>-1</sup>'],
            [u'{{Unité|10000|J||kg||m|-2}}', u'10 000 J⋅kg⋅m<sup>-2</sup>'],
            [u'{{Unité|-40.234|°C}}', u'-40.234 °C'],
#            [u'{{Unité|1.23456|e=9|J|2|K|3|s|-1}}', u'1.23456×10<sup>9</sup> J<sup>2</sup>⋅K<sup>3</sup>⋅s<sup>-1</sup>'],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.save(t[0]), t[1])

    def testFormatNum(self):
        tests=[
                [u"Elle comporte plus de {{formatnum:1000}} [[espèce]]s dans {{formatnum:90}}",u"Elle comporte plus de 1 000 [[espèce]]s dans 90"],
                ]
        for t in tests:
            self.assertEqual(self.sfrt.save(t[0]), t[1])

    def testJaponais(self):
        tests=[
                [u"{{Japonais|'''Happa-tai'''|はっぱ隊||Brigade des feuilles}}",u"'''Happa-tai''' (はっぱ隊, , Brigade des feuilles)"],
                [u"{{Japonais|'''Lolicon'''|ロリータ・コンプレックス|''rorīta konpurekkusu''}}, ou {{japonais|'''Rorikon'''|ロリコン}}",u"'''Lolicon''' (ロリータ・コンプレックス, ''rorīta konpurekkusu''), ou '''Rorikon''' (ロリコン)"],
                [u"Le {{japonais|'''Tōdai-ji'''|東大寺||littéralement « Grand temple de l’est »}}, de son nom complet {{japonais|Kegon-shū daihonzan Tōdai-ji|華厳宗大本山東大寺}}, est un",u"Le '''Tōdai-ji''' (東大寺, , littéralement « Grand temple de l’est »), de son nom complet Kegon-shū daihonzan Tōdai-ji (華厳宗大本山東大寺), est un"]
            ]

        for t in tests:
            self.assertEqual(self.sfrt.save(t[0]), t[1])

    def testNobr(self):
        tests=[
                [u"{{nobr|[[préfixe binaire|préfixes binaires]]}}",u"<span class=\"nowrap\">[[préfixe binaire|préfixes binaires]]</span>"],
                [u"{{nobr|93,13x2{{exp|30}} octets}}",u"<span class=\"nowrap\">93,13x2<sup>30</sup> octets</span>"]
            ]
        for t in tests:
            self.assertEqual(self.sfrt.save(t[0]), t[1])


    def testHeures(self):
        tests=[
                [u"{{heure|8}}",u"8 h"],
                [u"{{heure|22}}",u"22 h"],
                [u"{{heure|1|55}}",u"1 h 55"],
                [u"{{heure|10|5}}",u"10 h 5"],
                [u"{{heure|22|55|00}}",u"22 h 55 min 00 s"],
            ]
        for t in tests:
            self.assertEqual(self.sfrt.save(t[0]), t[1])


if __name__ == '__main__':
    unittest.main()
