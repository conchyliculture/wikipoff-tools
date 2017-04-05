#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 "Renzokuken" (pseudonym, first committer of WikipOff project) at
# https://github.com/conchyliculture/wikipoff
#
# This file is part of WikipOff.
#
#     WikipOff is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     WikipOff is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with WikipOff.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re
import locale


class WikiFRTranslator(object):
    @staticmethod
    def IsAllowedTitle(title):
        return title not in [
            u'Modèle', u'Catégorie', u'Portail', u'Fichier', u'Wikipédia',
            u'Projet', u'Référence', u'MediaWiki', u'Aide', u'Module']
    def __init__(self):
        # Templates that allow inclusion of }} in parameters will fail....
        # We should use the dropNested thing  maybe?
        # TODO
        self.fr_saveNobrTemplatesRE = re.compile(
            r'{{nobr\|((?:[^{]+)|(?:[^{]*{{[^}]+}}[^}]*))}}', re.IGNORECASE|re.UNICODE)
        self.fr_saveHeureTemplatesRE = re.compile(
            r'{{heure((\|(\d\d?))+)}}', re.IGNORECASE|re.UNICODE)
        self.fr_saveDateTemplatesRE = re.compile(
            r'{{date(?: de naissance| de décès)?\|(|\d+(?:er)?)\|([^|}]+)\|?(\d*)(?:\|[^}]+)?}}',
            re.IGNORECASE|re.UNICODE)
        self.fr_saveDateShortTemplatesRE = re.compile(
            r'{{1er (janvier|f.vrier|mars|avril|mai|juin|juillet|ao.t|septembre|octobre|novembre|d.cembre)}}',
            re.IGNORECASE|re.UNICODE)
        self.fr_saveLangTemplatesRE = re.compile(
            r'{{(lang(?:ue)?(?:-\w+)?(?:\|[^}\|]+)+)}}', re.IGNORECASE|re.UNICODE)
        self.fr_saveUnitsTemplatesRE = re.compile(
            r'{{(?:unit.|nombre|num|nau)\|([^|{}]+(?:\|[^{}|]*)*)}}', re.IGNORECASE|re.UNICODE)
        self.fr_saveTemperatureTemplatesRE = re.compile(
            r'{{tmp\|([^\|]+)\|°C}}', re.IGNORECASE|re.UNICODE)
        self.fr_saveRefIncTemplatesRE = re.compile(
            r'{{Référence [^|}]+\|([^|]+)}}', re.IGNORECASE) # incomplete/insuff/a confirmer/nécessaire
        self.fr_saveNumeroTemplatesRE = re.compile(
            r'{{(numéro|n°|nº)}}', re.IGNORECASE)
        self.fr_saveCitationTemplatesRE = re.compile(
            r'{{citation ?(?:bloc|nécessaire)?\|([^}]+)}}', re.IGNORECASE)
        self.fr_savePassageEvasifTemplatesRE = re.compile(
            r'{{passage évasif\|([^}]+)}}', re.IGNORECASE)
# not in my wikipedia
#self.fr_savePassNonNeutreTemplatesRE = re.compile(r'{{(?:passage non neutre|non neutre|nonneutre)\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_saveDouteuxTemplatesRE = re.compile(
            r'{{douteux\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_savePasspromotionnelTemplatesRE = re.compile(
            r'{{(?:passage promotionnel|pub !|promo !)\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_savePassIneditTemplatesRE = re.compile(
            r'{{passage inédit\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_savePasClairTemplatesRE = re.compile(
            r'{{pas clair\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_saveWTFTemplatesRE = re.compile(
            r'{{incomprénsible\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_savePrecNecTemplatesRE = re.compile(
            r'{{Précision nécessaire\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_saveQuoiTemplatesRE = re.compile(
            r'{{Quoi\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_savePourquoiTemplatesRE = re.compile(
            r'{{Pourquoi\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_saveCommentTemplatesRE = re.compile(
            r'{{Comment\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_saveWhereTemplatesRE = re.compile(
            r'{{Où\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_saveQuandTemplatesRE = re.compile(
            r'{{Quand\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_saveDepuisQuandTemplatesRE = re.compile(
            r'{{Depuis Quand\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_saveQuiQuoiTemplatesRE = re.compile(
            r'{{(?:Qui|Lequel|combien|enquoi|en quoi|lesquels|laquelle|lesquelles|par qui|parqui|pour qui)\|([^\|]+)}}',
            re.IGNORECASE)
        self.fr_savestyleTemplatesRE = re.compile(
            r'{{style\|([^\|]+)(?:\|[^}]+)?}}', re.IGNORECASE)
        self.fr_saveFormatnumTemplatesRE = re.compile(
            r'{{(?:formatnum):([0-9.,]+)}}', re.IGNORECASE)
        self.fr_saveWeirdNumbersTemplatesRE = re.compile(
            r'{{((?:(exp|ind)\|[^}]+)|\d|e|1er|1re|2nd|2nde)}}', re.IGNORECASE)
        self.fr_saveCouleursTemplatesRE = re.compile(
            r'{{(rouge|bleu|vert|jaune|orange|gris|marron|rose)\|([^\|}]+)}}', re.IGNORECASE)
        self.fr_saveCodeTemplatesRE = re.compile(
            r'{{code\|([^\|}]+)}}', re.IGNORECASE)
        self.fr_saveJaponaisTemplatesRE = re.compile(
            r'{{japonais\|([^\|]+)\|([^}]+)}}', re.IGNORECASE)
        self.fr_saveSimpleSieclesTempaltesRE = re.compile(
            r'{{([^}]+ (?:si.cle|mill.naire)[^}]*)}}', re.IGNORECASE|re.LOCALE)
        self.fr_saveSieclesTempaltesRE = re.compile(
            r'{{(?:([^|}]+(?:si.cle|mill.naire)[^|}]*)|(-?s2?-?(?:\|[^|}]+\|e)+))\|?}}',
            re.IGNORECASE)
        self.fr_saveSieclesGTempaltesRE = re.compile(
            r'{{(-?sp-?(\|[^|}]+\|er?\|[^|}]+\|[^|}]+\|er?\|?s?))}}', re.IGNORECASE)
        self.fr_saveNapoleonTemplatesRE = re.compile(
            r'{{(Napoléon I)er}}', re.IGNORECASE)

        self.aRE = re.compile(r'<math>')
        self.bRE = re.compile(r'</math>')
        self.locale_set = False


    def Translate(self, input_text):
        if not self.locale_set:
            locale.setlocale(locale.LC_ALL, u'fr_FR.utf-8')
            self.locale_set = True
        text = input_text
        text = self.fr_saveHeureTemplates(text)
        text = self.fr_saveNobrTemplates(text)
        text = self.fr_saveTemperatureTemplates(text)
        text = self.fr_saveFormatnumTemplates(text)
        text = self.fr_saveUnitsTemplates(text)
        text = self.fr_saveWeirdNumbersTemplates(text)
        text = self.fr_saveNumeroTemplate(text)
        text = self.fr_saveSieclesGTemplates(text)
        text = self.fr_saveSieclesTemplates(text)
        text = self.fr_saveLangTemplates(text)
        text = self.fr_saveCouleursTemplates(text)
        text = self.fr_saveRefIncTemplates(text)
        text = self.fr_saveDateTemplates(text)
        text = self.fr_saveQuiQuoiTemplates(text)
        text = self.fr_saveCodeTemplates(text)
        text = self.fr_saveCitationTemplate(text)
        text = self.fr_saveNapoleonTemplates(text)
        text = self.fr_saveDateShortTemplates(text)
        text = self.fr_saveJaponaisTemplates(text)
#        text = self.fr_savePasspromotionnelTemplates(text)
#        text = self.fr_savePassIneditTemplates(text)
#        text = self.fr_savePasClairTemplates(text)
#        text = self.fr_saveWTFTemplates(text)
#        text = self.fr_savePrecNecTemplates(text)
#        text = self.fr_savestyleTemplates(text)
        return text

    def replheures(self, m):
        res = ""
        t = m.group(1).split("|")
        l = len(t)
# HELLO I LOVE YOU CAN I HAVE SWITCH CASE FFS
        if l == 2:
            res = "%s h"%t[1]
        elif l == 3:
            res = "%s h %s"%(t[1], t[2])
        elif l == 4:
            res = "%s h %s min %s s"%(t[1], t[2], t[3])
        return res.strip()

    def fr_saveHeureTemplates(self, text):
        return re.sub(self.fr_saveHeureTemplatesRE, self.replheures, text)

    def replnobr(self, m):
        pute = m.group(1)
        return "<span class=\"nowrap\">%s</span>"%pute

    def fr_saveNobrTemplates(self, text):
        #return self.fr_saveNobrTemplatesRE.sub(r'\1', text)
        #return self.fr_saveNobrTemplatesRE.sub(r'<span class="nowrap">\1</span>', text)
        return re.sub(self.fr_saveNobrTemplatesRE, self.replnobr, text)

    def fr_saveNapoleonTemplates(self, text):
        return self.fr_saveNapoleonTemplatesRE.sub(r'Napoléon I<sup>er</sup>', text)

    def fr_saveDouteuxTemplates(self, text):
        return self.fr_saveDouteuxTemplatesRE.sub(r'\1<sup>[douteux]</sup>', text)

    def fr_savePasspromotionnelTemplates(self, text):
        return self.fr_savePasspromotionnelTemplatesRE.sub(
            r'\1<sup>[passage promotionnel]</sup>', text)

    def fr_savePassIneditTemplates(self, text):
        return self.fr_savePassIneditTemplatesRE.sub(
            r'\1<sup>[interprétion personnelle]</sup>', text)

    def fr_savePasClairTemplates(self, text):
        return self.fr_savePasClairTemplatesRE.sub(r'\1<sup>[pas clair]</sup>', text)

    def fr_saveWTFTemplates(self, text):
        return self.fr_saveWTFTemplatesRE.sub(r'\1<sup>[incomprénsible]</sup>', text)

    def fr_savePrecNecTemplates(self, text):
        return self.fr_savePrecNecTemplatesRE.sub(r'\1<sup>[précision néssaire]</sup>', text)

    def fr_saveQuiQuoiTemplates(self, text):
        return self.fr_saveQuiQuoiTemplatesRE.sub(r'\1', text)

    def fr_savestyleTemplates(self, text):
        return self.fr_savestyleTemplatesRE.sub(r'\1', text)

    def replsiecles(self, m):
        nb = m.group(2)
        if nb:
            try:
                avjc = u''
                a, b, c = nb.split(u'|', 2)
                if a.startswith(u'-'):
                    avjc = u' av. J.-C. '
                if a.startswith(u's2'):
                    _, d, _ = c.split(u'|')
                    return b+u'e et '+d+u'e siècles'+avjc
                elif a.startswith(u'-s2'):
                    _, d, _ = c.split(u'|')
                    return b+u'e et '+d+u'e siècles'+avjc

                else:
                    return b+u'e siècle'+avjc
            except ValueError:
                # Failing humbly...
                return nb
        else:
            nb = m.group(1)
            return nb

    def fr_saveSieclesTemplates(self, text):
        return re.sub(self.fr_saveSieclesTempaltesRE, self.replsiecles, text)

    def replgsiecles(self, m):
        nb = m.group(1)
        res = u''
        if nb:
            try:
                a, b, c, d, e, f = nb.split(u'|', 5)
                if a.startswith(u'-'):
                    res = u' av. J.-C.'
                index = f.find(u'|')
                si = u'siècle'
                if index > 0:
                    f, s = f.split(u'|')
                    if s != u'':
                        si = u'siècles'

                return u'%s%s %s %s%s %s%s'%(b, c, d, e, f, si, res)
            except ValueError as e:
                raise e
                # Failing humbly...
                #return nb
#        else:
#            nb = m.group(1)
#            return nb

    def fr_saveSieclesGTemplates(self, text):
        return re.sub(self.fr_saveSieclesGTempaltesRE, self.replgsiecles, text)

    def fr_saveSimpleSieclesTemplates(self, text):
        return self.fr_saveSimpleSieclesTempaltesRE.sub(r'\1', text, re.LOCALE)

    def fr_saveCitationTemplate(self, text):
        return self.fr_saveCitationTemplatesRE.sub(r'«&#160;<i>\1</i>&#160;»', text)

    def fr_savePassageEvasifTemplates(self, text):
        return self.fr_savePassageEvasifTemplatesRE.sub(r'<u>\1</u><sup>[evasif??]</sup>', text)

    def fr_saveNumeroTemplate(self, text):
        return self.fr_saveNumeroTemplatesRE.sub(u"n°", text)

    def fr_saveRefIncTemplates(self, text):
        return self.fr_saveRefIncTemplatesRE.sub(r'<u>\1</u><sup>[ref incomplète??]</sup>', text)

    def repldate(self, m):
        res = u''
        if m.group(1) == u'':
            res = u'%s %s'%(m.group(2), m.group(3))
        elif m.group(1) == u'1':
            res = u'1er %s %s'%(m.group(2).lstrip(), m.group(3))
        else:
            res = u'%s %s %s'%(m.group(1), m.group(2).lstrip(), m.group(3))
        return res.strip()

    def fr_saveDateTemplates(self, text):
        return re.sub(self.fr_saveDateTemplatesRE, self.repldate, text)

    def fr_saveDateShortTemplates(self, text):
        return self.fr_saveDateShortTemplatesRE.sub(r'1<sup>er</sup> \1', text)

    def repllang(self, m):
        lol = m.group(1).split(u'|')
        if re.match(r'.*\[\[.+\|.+\]\]', m.group(0)):
            return u'|'.join(lol[2:])

        if re.match(r'lang-\w+', lol[0], re.IGNORECASE):
            return lol[1]
        else:
            reste = lol[2:]
            if len(reste) == 1:
                return reste[0].replace(u'texte=', u'')
            else:
                for p in reste:
                    coin = re.match(r'texte=(.*)', p, re.IGNORECASE)
                    if coin:
                        return coin.group(1)


    def fr_saveLangTemplates(self, text):
        return re.sub(self.fr_saveLangTemplatesRE, self.repllang, text)

    def replcolors(self, m):
        col = m.group(1)
        t = m.group(2)
        if col.lower == u'rouge':
            return u'<font color=\'red\'>%s</font>'%t
        elif col.lower == u'bleu':
            return u'<font color=\'blue\'>%s</font>'%t
        elif col.lower == u'vert':
            return u'<font color=\'green\'>%s</font>'%t
        elif col.lower == u'jaune':
            return u'<font color=\'yellow\'>%s</font>'%t
        elif col.lower == u'orange':
            return u'<font color=\'orange\'>%s</font>'%t
        elif col.lower == u'gris':
            return u'<font color=\'grey\'>%s</font>'%t
        elif col.lower == u'marron':
            return u'<font color=\'brown\'>%s</font>'%t
        elif col.lower == u'rose':
            return u'<font color=\'pink\'>%s</font>'%t
        else:
            return t

    def fr_saveCodeTemplates(self, text):
        return self.fr_saveCodeTemplatesRE.sub(
            r'<span style=\"font-family:monospace, Courier\">\1</span>', text)

    def fr_saveTemperatureTemplates(self, text):
        return self.fr_saveTemperatureTemplatesRE.sub(r'\1°C', text)

    def repljaponais(self, m):
        return m.group(1)+u' ('+m.group(2).replace(u'|', u', ').replace(u'extra=', u'')+u')'

    def fr_saveJaponaisTemplates(self, text):
        return re.sub(self.fr_saveJaponaisTemplatesRE, self.repljaponais, text)

    def fr_saveCouleursTemplates(self, text):
        return re.sub(self.fr_saveCouleursTemplatesRE, self.replcolors, text)

    def replweirdnum(self, m):
        nb = m.group(1)
        if nb.find(u'|') >= 0:
            lol, nb = nb.split(u'|', 1)
            if lol == u'exp':
                return u'<sup>%s</sup>'%nb
            elif lol == u'ind':
                return u'<sub>%s</sub>'%nb
        else:
            if nb == u'e':
                return u'<sup>e</sup>'
            elif nb == u'1er':
                return u'1<sup>er</sup>'
            elif nb == u'1re':
                return u'1<sup>re</sup>'
            elif nb == u'2nd':
                return u'2<sup>nd</sup>'
            elif nb == U'2NDE':
                return u'2<sup>de</sup>'
            else:
                return u'<sup>%s</sup>'%nb

    def fr_saveWeirdNumbersTemplates(self, text):
        return re.sub(self.fr_saveWeirdNumbersTemplatesRE, self.replweirdnum, text)

    def replformat(self, m):
        nb = m.group(1)
        try:
            if nb:
                if nb.find(u'.') > 0 or nb.find(u',') > 0:
                    return locale.format(u'%f', float(nb), grouping=True)
                else:
                    return locale.format(u'%d', int(nb), grouping=True)
        except ValueError:
            # Failing humbly...
            return nb

    def fr_saveFormatnumTemplates(self, text):
        return re.sub(self.fr_saveFormatnumTemplatesRE, self.replformat, text)

    def num_to_loc(self, num):
        try:
            virg = num.replace(u' ', u'').replace(u',', u'.').split(r'.')
            res = locale.format(u'%d', int(virg[0]), grouping=True)
            if len(virg) > 1:
                res += u'.' + virg[1]
            return res
        except ValueError:
            # Failing humbly...
            return num

    def replunit(self, m):
        l = m.group(1).split('|')
        if len(l) == 1:
            a = self.num_to_loc(l[0])
            return u'%s'%(a)
        else:
            # It becomes clear in the test function testUnit below THAT THIS IS A FUCKING MESS
            dot = u''
            exp = u' '
            tab = []
            for s in l[1:]:
                index = s.find(u'=')
                if index > 0:
                    s = s[2:]
                    exp = u'×10'
                if re.match(r'-?[0-9]', s):
                    tab.append(u'%s<sup>%s</sup>'%(dot, self.num_to_loc(s)))
                elif s == u'':
                    tab.append(dot)
                else:
                    dot = s
            res = self.num_to_loc(l[0]) + exp
            if len(tab) == 0:
                res += dot
            elif len(tab) == 1:
                res += tab[0]
            else:
                res += u'⋅'.join(tab)
                res = re.sub(r'×10<sup>([^<]+)</sup>', r'×10<sup>\1</sup> ', res)
            return res

    def fr_saveUnitsTemplates(self, text):
        return re.sub(self.fr_saveUnitsTemplatesRE, self.replunit, text)
