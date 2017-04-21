#!/usr/bin/python
# encoding: utf-8

from __future__ import unicode_literals

import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), u'..'))
sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        u'..', u'lib', u'python{0:d}.{1:d}'.format(
            sys.version_info.major, sys.version_info.minor),
        u'site-packages'))
from binascii import unhexlify
import codecs
import locale
import unittest
from lib.writer.compress import LzmaCompress
from lib.writer.sqlite import OutputSqlite
from lib.wikimedia.converter import WikiConverter
from lib.wikimedia.languages import wikifr
from lib.wikimedia.XMLworker import XMLworker

locale.setlocale(locale.LC_ALL, u'fr_FR.utf-8')


class TestCompression(unittest.TestCase):

    def test_lzma(self):
        data = u'['+u'oléléolala'*12+u']'

        compressed = LzmaCompress(data)
        expected_compressed = unhexlify(
            u'5d000080009200000000000000002d9bc98c53caed25d8aa1da643a8fa430000')
        self.assertEqual(expected_compressed, compressed)

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
        res = o.GetMetadata()
        date = res.pop(u'date')
        self.assertIsNotNone(date, None)
        version = res.pop(u'version')
        self.assertIsNotNone(version, None)

        self.assertEqual(good_tags, res)


    def test_AddRedirect(self):
        o = OutputSqlite(None)
        test_redirect = (u'From', u'To')
        o.AddRedirect(*test_redirect)
        o._AllCommit()

        o.cursor.execute(u'SELECT * FROM redirects')
        self.assertEqual(test_redirect, o.cursor.fetchone())

    def test_AddArticle(self):
        o = OutputSqlite(None)
        test_article = (
            u'This title &  à_è>Ýü',
            (u"{{Japonais|'''Lolicon'''|ロリータ・コンプレックス|"
             u"''rorīta konpurekkusu''}}, ou {{japonais|'''Rorikon'''|ロリコン}}")
            )
        o.AddArticle(*test_article)
        o._AllCommit()

        o.cursor.execute(u'SELECT * FROM articles')
        self.assertEqual((1, test_article[0], test_article[1]), o.cursor.fetchone())

    def test_Close(self):
        o = OutputSqlite(None)
        test_article = (
            u'This title &  à_è>Ýü',
            (u"{{Japonais|'''Lolicon'''|ロリータ・コンプレックス|"
             u"''rorīta konpurekkusu''}}, ou {{japonais|'''Rorikon'''|ロリコン}}"))
        o.AddArticle(*test_article)
        test_redirect = (u'From', u'To')
        o.AddRedirect(*test_redirect)
        o._AllCommit()
        o.Close()

class TestWIkiFr(unittest.TestCase):
    sfrt = wikifr.WikiFRTranslator()

    def testLang(self):
        tests = [
            [u"lolilol ''{{lang|la|domus Dei}}''", u"lolilol ''domus Dei''"],
            [u"''{{lang-en|Irish Republican Army}}, IRA'' ; ''{{lang-ga|Óglaigh na hÉireann}}'') est le nom porté",
             u"''Irish Republican Army, IRA'' ; ''Óglaigh na hÉireann'') est le nom porté"],
            [u"{{lang|ko|입니다.}}", u"입니다."],
            [u"Ainsi, le {{lang|en|''[[Quicksort]]''}} (ou tri rapide)",
             u"Ainsi, le ''[[Quicksort]]'' (ou tri rapide)"],
            [u" ''{{lang|hy|Hayastan}}'', {{lang|hy|Հայաստան}} et ''{{lang|hy|Hayastani Hanrapetut’yun}}'', {{lang|hy|Հայաստանի Հանրապետություն}}",
             u" ''Hayastan'', Հայաստան et ''Hayastani Hanrapetut’yun'', Հայաստանի Հանրապետություն"],
            [u"{{langue|ja|酸度}} || １.４（{{langue|ja|芳醇}}", u"酸度 || １.４（芳醇"],
            [u"{{langue|thaï|กรุงเทพฯ}}", u"กรุงเทพฯ"],
            [u"{{Lang|ar|texte=''Jabal ad Dukhan''}}", u"''Jabal ad Dukhan''"],
            [u"{{lang|arc-Hebr|dir=rtl|texte=ארמית}} {{lang|arc-Latn|texte=''Arāmît''}},}}",
             u"ארמית ''Arāmît'',}}"],
            [u"ce qui augmente le risque de {{lang|en|''[[Mémoire virtuelle#Swapping|swapping]]''}})",
             u"ce qui augmente le risque de ''[[Mémoire virtuelle#Swapping|swapping]]'')"]
        ]

        for t in tests:
            self.assertEqual(self.sfrt.Translate(t[0]), t[1])

    def testDateShort(self):
        tests = [
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
            self.assertEqual(self.sfrt.Translate(t[0]), t[1])

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
            self.assertEqual(self.sfrt.Translate(t[0]), t[1])

    def testSimpleSiecle(self):
        tests = [
            [u'{{Ier siècle}}, {{IIe siècle}}, ... {{XXe siècle}}, ...', u'Ier siècle, IIe siècle, ... XXe siècle, ...'],
            [u'{{Ier siècle av. J.-C.}}, {{IIe siècle av. J.-C.}}, ...', u'Ier siècle av. J.-C., IIe siècle av. J.-C., ...'],
            [u'{{Ier millénaire}}, {{IIe millénaire}}, ...', u'Ier millénaire, IIe millénaire, ...'],
            [u'{{Ier millénaire av. J.-C.}}, {{IIe millénaire av. J.-C.}}, ...', u'Ier millénaire av. J.-C., IIe millénaire av. J.-C., ...'],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.Translate(t[0]), t[1])

    def testGSiecles(self):
        tests = [
            [u'{{sp|VII|e|ou|VIII|e|}}', u'VIIe ou VIIIe siècle'],
            [u'{{sp-|VII|e|ou|VIII|e|}}', u'VIIe ou VIIIe siècle'],
            [u'{{-sp|IX|e|-|VII|e|s}}', u'IXe - VIIe siècles av. J.-C.'],
            [u'{{-sp-|IX|e|-|VII|e|s}}', u'IXe - VIIe siècles av. J.-C.'],
            [u'au {{sp-|XII|e|et au|XVI|e}}', u'au XIIe et au XVIe siècle'],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.Translate(t[0]), t[1])

    def testTemperature(self):
        tests = [
            [u'température supérieure à {{tmp|10|°C}}.', u'température supérieure à 10°C.'],
            [u'Il se décompose de façon explosive aux alentours de {{tmp|95|°C}}.', u'Il se décompose de façon explosive aux alentours de 95°C.'],
            [u'Entre 40 et {{tmp|70|°C}}', u'Entre 40 et 70°C'],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.Translate(t[0]), t[1])

    def testSiecle(self):
        tests = [
            ["{{s|III|e}}", u"IIIe siècle"],
            ["{{-s|III|e}}", u"IIIe siècle av. J.-C. "],
            ["{{s-|III|e}}", u"IIIe siècle"],
            ["{{-s-|III|e}}", u"IIIe siècle av. J.-C. "],
            ["{{s2|III|e|IX|e}}", u"IIIe et IXe siècles"],
            ["{{-s2|III|e|IX|e}}", u"IIIe et IXe siècles av. J.-C. "],
            ["{{s2-|III|e|IX|e}}", u"IIIe et IXe siècles"],
            ["{{-s2-|III|e|IX|e}}", u"IIIe et IXe siècles av. J.-C. "],
            [u"{{s-|XIX|e|}}", u"XIXe siècle"],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.Translate(t[0]), t[1])

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
            # [u'{{Unité|1.23456|e=9|J|2|K|3|s|-1}}', u'1.23456×10<sup>9</sup> J<sup>2</sup>⋅K<sup>3</sup>⋅s<sup>-1</sup>'],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.Translate(t[0]), t[1])

    def testFormatNum(self):
        tests = [
            [u'Elle comporte plus de {{formatnum:1000}} [[espèce]]s dans {{formatnum:90}}',
             u'Elle comporte plus de 1 000 [[espèce]]s dans 90'],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.Translate(t[0]), t[1])

    def testJaponais(self):
        tests = [
            [u"{{Japonais|'''Happa-tai'''|はっぱ隊||Brigade des feuilles}}",
             u"'''Happa-tai''' (はっぱ隊, , Brigade des feuilles)"],
            [u"{{Japonais|'''Lolicon'''|ロリータ・コンプレックス|''rorīta konpurekkusu''}}, ou {{japonais|'''Rorikon'''|ロリコン}}",
             u"'''Lolicon''' (ロリータ・コンプレックス, ''rorīta konpurekkusu''), ou '''Rorikon''' (ロリコン)"],
            [u"Le {{japonais|'''Tōdai-ji'''|東大寺||littéralement « Grand temple de l’est »}}, de son nom complet {{japonais|Kegon-shū daihonzan Tōdai-ji|華厳宗大本山東大寺}}, est un",
             u"Le '''Tōdai-ji''' (東大寺, , littéralement « Grand temple de l’est »), de son nom complet Kegon-shū daihonzan Tōdai-ji (華厳宗大本山東大寺), est un"]
        ]

        for t in tests:
            self.assertEqual(self.sfrt.Translate(t[0]), t[1])

    def testNobr(self):
        tests = [
            [u'{{nobr|[[préfixe binaire|préfixes binaires]]}}',
             u'<span class="nowrap">[[préfixe binaire|préfixes binaires]]</span>'],
            [u'{{nobr|93,13x2{{exp|30}} octets}}',
             u'<span class="nowrap">93,13x2<sup>30</sup> octets</span>']
        ]

        for t in tests:
            self.assertEqual(self.sfrt.Translate(t[0]), t[1])


    def testHeures(self):
        tests = [
            [u'{{heure|8}}', u'8 h'],
            [u'{{heure|22}}', u'22 h'],
            [u'{{heure|1|55}}', u'1 h 55'],
            [u'{{heure|10|5}}', u'10 h 5'],
            [u'{{heure|22|55|00}}', u'22 h 55 min 00 s'],
        ]
        for t in tests:
            self.assertEqual(self.sfrt.Translate(t[0]), t[1])

    def test_allowed_title(self):
        self.assertEqual(False, self.sfrt.IsAllowedTitle(u'Modèle'))
        self.assertEqual(True, self.sfrt.IsAllowedTitle(u'Lolilol'))

class TestXMLworkerClass(XMLworker):

    def __init__(self, input_file, output_array):
        super(TestXMLworkerClass, self).__init__(input_file)
        self.GENERATED_STUFF = output_array

    def GenerateMessage(self, title, body, msgtype):
        self.GENERATED_STUFF.append({u'type': msgtype, u'title': title, u'body': body})

class TestXMLworker(unittest.TestCase):

    def setUp(self):
        self.GENERATED_STUFF = []
        self.xmlw = TestXMLworkerClass(
            os.path.join(
                os.path.dirname(__file__), u'test_data',
                u'frwiki-latest-pages-articles.xml.short'),
            self.GENERATED_STUFF)

        self.xmlw._ProcessData()

    def test_GetInfos(self):
        self.maxDiff = None
        expected_infos = {
            u'lang': u'fr',
            u'generator': u'MediaWiki 1.29.0-wmf.18',
            u'author': u'renzokuken @ Wikipoff-tools',
            u'sitename': u'Wikipédia',
            u'lang-english': u'French',
            u'lang-local': u'Français',
            u'source': u'https://fr.wikipedia.org/wiki/Wikip%C3%A9dia:Accueil_principal',
            u'base': u'https://fr.wikipedia.org/wiki/Wikip%C3%A9dia:Accueil_principal',
            u'lang-code': u'fr',
            u'type': u'Wikipédia',
            u'dbname': u'frwiki'}
        self.assertEqual(expected_infos, self.xmlw.db_metadata)

    def test_wikitype(self):
        self.assertEqual(u'wikipedia', self.xmlw.wikitype)

    def test_ProcessData(self):
        self.xmlw._ProcessData()

        generated_redirect = self.GENERATED_STUFF[10]
        self.assertEqual(
            u'Sigles en médecine', generated_redirect[u'title'])
        self.assertEqual(
            u'Liste d\'abréviations en médecine', generated_redirect[u'body'])
        self.assertEqual(1, generated_redirect[u'type'])

        generated_article = self.GENERATED_STUFF[-1]
        self.assertEqual(
            u'Aude (département)', generated_article[u'title'])
        self.assertEqual(
            u'{{Voir homonymes|Aude}}\n{{Infobox Département de France',
            generated_article[u'body'][0:55])
        self.assertEqual(17357, len(generated_article[u'body']))
        self.assertEqual(2, generated_article[u'type'])

        generated_article_colon_allowed = self.GENERATED_STUFF[-2]
        self.assertEqual(
            u'Race:Chie', generated_article_colon_allowed[u'title'])
        self.assertEqual(
            u'osef ', generated_article_colon_allowed[u'body'])
        self.assertEqual(2, generated_article_colon_allowed[u'type'])

        generated_article_colon_notallowed = self.GENERATED_STUFF[-3]
        self.assertEqual(u'Aube (département)', generated_article_colon_notallowed[u'title'])


class TestConverterNoLang(unittest.TestCase):

    def test_thumbstuff(self):
        self.maxDiff = None
        wikicode = u'[[Figure:Sahara satellite hires.jpg|thumb|right|300px|Foto dal satelit]] Il \'\'\'Sahara\'\'\' ([[Lenghe arabe|arap]] صحراء {{audio|ar-Sahara.ogg|pronuncie}}, \'\'desert\'\') al è un [[desert]] di gjenar tropicâl inte [[Afriche]] dal nord. Al è il secont desert plui grant dal mont (daspò la [[Antartide]]), cuntune superficie di 9.000.000 km².'
        expected = u' Il <b>Sahara</b> (<a href="Lenghe arabe">arap</a> صحراء , <i>desert</i> ) al è un <a href="desert">desert</a> di gjenar tropicâl inte <a href="Afriche">Afriche</a> dal nord. Al è il secont desert plui grant dal mont (daspò la <a href="Antartide">Antartide</a>), cuntune superficie di 9.000.000 km².'
        c = WikiConverter()
        body = c.Convert(u'title', wikicode)[1]
        self.assertEqual(expected, body)


class TestConverterFR(unittest.TestCase):

    def setUp(self):
        self.GENERATED_STUFF = []
        self.xmlw = TestXMLworkerClass(
            os.path.join(
                os.path.dirname(__file__), u'test_data',
                u'frwiki-latest-pages-articles.xml.short'),
            self.GENERATED_STUFF)
        self.xmlw._ProcessData()

    def test_ShortConvert(self):
        self.maxDiff = None
        wikicode = (
            u'le [[lis martagon|lis des Pyrénées]], \'\'[[Calotriton asper]]\'\''
            u'ou la [[Equisetum sylvaticum|prêle des bois]]')
        expected = (
            u'le <a href="lis martagon">lis des Pyrénées</a>, <i><a href="Calotriton asper">'
            u'Calotriton asper</a></i> ou la <a href="Equisetum sylvaticum">prêle des bois</a>')
        c = WikiConverter(u'wikipedia', u'fr')
        body = c.Convert(u'title', wikicode)[1]
        self.assertEqual(expected, body)

    def test_ConvertArticle(self):
        self.maxDiff = None
        c = WikiConverter(u'wikipedia', u'fr')
        a = self.GENERATED_STUFF[-1]
        (_, body) = c.Convert(a[u'title'], a[u'body'])
        body = body.strip()
        # with open(u'/tmp/lolilol', u'wb') as w:
        #w.write(body.encode(u'utf-8'))
        expected_html_path = os.path.join(os.path.dirname(__file__), u'test_data', u'aude.html')
        with codecs.open(expected_html_path, u'r', encoding=u'utf-8') as html:
            test_data = html.read().strip()
            self.assertEqual(len(test_data), len(body))
            self.assertEqual(test_data, body)


if __name__ == '__main__':
    unittest.main()
