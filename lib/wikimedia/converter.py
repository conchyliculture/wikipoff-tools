# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
import sys
import lib.wikimedia.wikiglobals as wikiglobals
from lib.wikimedia import wikitools
try:
    from htmlentitydefs import name2codepoint
except:
    from html.entities import name2codepoint


class WikiConverter(object):

    # Matches bold/italic
    BOLD_ITALIC_RE = re.compile(r"'''''([^']*?)'''''")
    BOLD_RE = re.compile(r"'''(.*?)'''")
    ITALIC_QUOTE_RE = re.compile(r'\'\'"(.*?)"\'\'')
    ITALIC_RE = re.compile(r'\'\'([^\']*)\'\'')
    QUOTE_QUOTE_RE = re.compile(r'""(.*?)""')

    # Matches space
    SPACES_RE = re.compile(r' {2,}')
    # Match preformatted lines
    PREFORMATED_RE = re.compile(r'^ .*?$', re.MULTILINE)

    # Matches dots
    DOTS_RE = re.compile(r'\.{4,}')
    # Match external links (space separates second optional parameter)
    EXTERNAL_LINK_RE = re.compile(r'\[\w+.*? (.*?)\]')
    EXTERNAL_LINK_NO_ANCHOR_RE = re.compile(r'\[\w+[&\]]*\]')
    PARAMETRIZED_RE = re.compile(r'\[\[.*?\]\]')
    TOOMANYBR_RE = re.compile(r'<br/>(<br/>(?:<br/>)+)')
    WIKI_LINK_RE = re.compile(r'\[\[([^[]*?)(?:\|([^[]*?))?\]\](\w*)')
    # Match list stars
    LIST_RE = re.compile(r'^\*+')

    # Match HTML comments
    COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)

    SECTION_RE = re.compile(r'(==+)\s*(.*?)\s*\1')

    def __init__(self, wikitype=None, wikilang=None):
        self.translator = wikitools.GetLanguageModule(wikitype, wikilang)

        # Match selfClosing HTML tags
        self.selfClosing_tag_patterns = []
        for tag in wikiglobals.self_closing_tags:
            pattern = re.compile(r'<\s*%s\b[^/]*/\s*>' % tag, re.DOTALL | re.IGNORECASE)
            self.selfClosing_tag_patterns.append(pattern)

        # Match HTML placeholder tags
        self.placeholder_tag_patterns = []
        for tag, repl in wikiglobals.placeholder_tags.items():
            pattern = re.compile(
                r'<\s*%s(\s*| [^>]+?)>.*?<\s*/\s*%s\s*>' % (tag, tag),
                re.DOTALL | re.IGNORECASE)
            self.placeholder_tag_patterns.append((pattern, repl))

        self.ignored_tag_patterns = []
        for tag in wikiglobals.ignored_tags:
            left = re.compile(r'<\s*%s\b[^>]*>' % tag, re.IGNORECASE)
            right = re.compile(r'<\s*/\s*%s>' % tag, re.IGNORECASE)
            self.ignored_tag_patterns.append((left, right))

        self.discard_element_patterns = []
        for tag in wikiglobals.discard_elements:
            pattern = re.compile(
                r'<\s*%s\b[^>]*>.*?<\s*/\s*%s>' % (tag, tag), re.DOTALL | re.IGNORECASE)
            self.discard_element_patterns.append(pattern)

    def compact(self, text):
        """Deal with headers, lists, empty sections, residuals of tables"""
        page = []                   # list of paragraph
        headers = {}                # Headers for unfilled sections
        emptySection = False        # empty sections are discarded
        inList = 0              # whether opened <UL>

        for line in text.split(u'\n'):
            if not line:
                if inList > 0:
                    page.append(u'</ul>' * inList)
                    inList = 0
                page.append(u'<br/><br/>') # for lisibility
                continue
            # Handle section titles
            m = WikiConverter.SECTION_RE.match(line)
            if m:
                title = m.group(2)
                lev = len(m.group(1))
                if wikiglobals.keep_sections:
                    page.append(u'<h%d>%s</h%d>' % (lev, title, lev))
                else:
                    if title and title[-1] not in u'!?':
                        title += u'.'
                headers[lev] = title
                # drop previous headers
    #            for i, _ in headers.items():
    #                if i > lev:
    #                    del headers[i]V
                headers = {k:v for k, v in headers.items() if k <= lev}
                emptySection = True
                continue
            # Handle page title
            if line.startswith(u'++'):
                title = line[2:-2]
                if title:
                    if title[-1] not in u'!?':
                        title += u'.'
                    page.append(title)
            # handle lists
            elif line[0] in u'*#:;':
                try:
                    if wikiglobals.keepSections:
                        listdepth = len(WikiConverter.LIST_RE.search(line).group())
                        if listdepth > inList:
                            page.append(u'<ul>' * (listdepth - inList))
                        elif listdepth < inList:
                            page.append(u'</ul>' * (inList - listdepth))
                        inList = listdepth
                        page.append(u'<li>%s</li>' % line[inList:])
                    else:
                        continue
                except AttributeError:
                    page.append(line)
            # Drop residuals of lists
            elif line[0] in u'{|' or line[-1] in u'}':
                continue
            # Drop irrelevant lines
            elif (line[0] == u'(' and line[-1] == u')') or line.strip(u'.-') == u'':
                continue
            elif len(headers):
    #            items = headers.items()
    #            items.sort()
                sorted(headers)
    #            for (i, v) in items:
    #                page.append(v)
                headers.clear()
                page.append(line)   # first line
                emptySection = False
            elif not emptySection:
                page.append(line)

        return page

    def Convert(self, title, text):
        buff = u''
        text = self._Clean(text)
        for line in self.compact(text):
            buff += line
        buff = WikiConverter.TOOMANYBR_RE.sub(r'<br/><br/>', buff)
        buff = buff.replace(u'<math>', u'\(')
        buff = buff.replace(u'</math>', u'\)')

        return (title, buff)

    def _Clean(self, input_text):
        if self.translator:
            text = self.translator.Translate(input_text)

        # Drop transclusions (template, parser functions)
        # See: http://www.mediawiki.org/wiki/Help:Templates
        text = self._DropNested(text, r'{{', r'}}')

        # Drop tables
        text = self._DropNested(text, r'{\|', r'\|}')

        # Expand links
        text = WikiConverter.WIKI_LINK_RE.sub(self._MakeAnchorTag, text)
        # Drop all remaining ones
        text = WikiConverter.PARAMETRIZED_RE.sub('', text)

        # Handle external links
        text = WikiConverter.EXTERNAL_LINK_RE.sub(r'\1', text)
        text = WikiConverter.EXTERNAL_LINK_NO_ANCHOR_RE.sub('', text)

        # Handle bold/italic/quote
        text = WikiConverter.BOLD_ITALIC_RE.sub(r'<i>\1</i>', text)
        text = WikiConverter.BOLD_RE.sub(r'<b>\1</b>', text)
        text = WikiConverter.ITALIC_QUOTE_RE.sub(r'&quot;\1&quot;', text)
        text = WikiConverter.ITALIC_RE.sub(r'<i>\1</i> ', text)
        text = WikiConverter.QUOTE_QUOTE_RE.sub(r'\1', text)
        text = text.replace(u'\'\'\'', u'').replace(u'\'\'', u'&quot;')

        ################ Process HTML ###############

        # turn into HTML
        text = self._Unescape(text)
        # do it again (&amp;nbsp;)
        text = self._Unescape(text)

        # Collect spans

        matches = []
        # Drop HTML comments
        for m in WikiConverter.COMMENT_RE.finditer(text):
            matches.append((m.start(), m.end()))

        # Drop self-closing tags
        for pattern in self.selfClosing_tag_patterns:
            for m in pattern.finditer(text):
                matches.append((m.start(), m.end()))

        # Drop ignored tags
        for left, right in self.ignored_tag_patterns:
            for m in left.finditer(text):
                matches.append((m.start(), m.end()))
            for m in right.finditer(text):
                matches.append((m.start(), m.end()))

        # Bulk remove all spans
        text = self._DropSpans(matches, text)

        # Cannot use dropSpan on these since they may be nested
        # Drop discarded elements
        for pattern in self.discard_element_patterns:
            text = pattern.sub(u'', text)

        # Expand placeholders
        for pattern, placeholder in self.placeholder_tag_patterns:
            index = 1
            for match in pattern.finditer(text):
                text = text.replace(match.group(), u'%s_%d' % (placeholder, index))
                index += 1

        # WTF ?
        #text = text.replace(u'<<', u'Â«').replace(u'>>', u'Â»')

        #############################################

        # Drop preformatted
        # This can't be done before since it may remove tags
#        text = WikiConverter.PREFORMATED_RE.sub(u'', text)

        # Cleanup text
        text = text.replace(u'\t', u' ')
        text = WikiConverter.SPACES_RE.sub(u' ', text)
        text = WikiConverter.DOTS_RE.sub(u'...', text)
        text = re.sub(u' (,:\.\)\]Â»)', r'\1', text)
        text = re.sub(u'(\[\(Â«) ', r'\1', text)
        text = re.sub(r'\n\W+?\n', '\n', text) # lines with only punctuations
        text = text.replace(u',,', u',').replace(u',.', u'.')
        return text

    def _DropNested(self, text, openDelim, closeDelim):
        openRE = re.compile(openDelim)
        closeRE = re.compile(closeDelim)
        # partition text in separate blocks { } { }
        matches = []                # pairs (s, e) for each partition
        nest = 0                    # nesting level
        start = openRE.search(text, 0)
        if not start:
            return text
        end = closeRE.search(text, start.end())
        next_ = start
        while end:
            next_ = openRE.search(text, next_.end())
            if not next_:            # termination
                while nest:         # close all pending
                    nest -= 1
                    end0 = closeRE.search(text, end.end())
                    if end0:
                        end = end0
                    else:
                        break
                matches.append((start.start(), end.end()))
                break
            while end.end() < next_.start():
                # { } {
                if nest:
                    nest -= 1
                    # try closing more
                    last = end.end()
                    end = closeRE.search(text, end.end())
                    if not end:     # unbalanced
                        if matches:
                            span = (matches[0][0], last)
                        else:
                            span = (start.start(), last)
                        matches = [span]
                        break
                else:
                    matches.append((start.start(), end.end()))
                    # advance start, find next close
                    start = next_
                    end = closeRE.search(text, next_.end())
                    break           # { }
            if next_ != start:
                # { { }
                nest += 1
        # collect text outside partitions
        res = u''
        start = 0
        for s, e in  matches:
            res += text[start:s]
            start = e
        res += text[start:]
        return res

    # Function applied to wikiLinks
    def _MakeAnchorTag(self, match):
        link = match.group(1)
        colon = link.find(':')
        # TODO parameter this shit
        if colon > 0:
            link_class = link[0:colon]
            if not self.translator.IsAllowedTitle(link_class):
                return u''
        trail = match.group(3)
        anchor = match.group(2)
        if not anchor:
            anchor = link
        anchor += trail
        if wikiglobals.keep_links:
            return u'<a href="%s">%s</a>' % (link, anchor)
        else:
            return anchor
    ##
    # Removes HTML or XML character references and entities from a text string.
    #
    # @param text The HTML (or XML) source text.
    # @return The plain text, as a Unicode string, if necessary.

    def _Unescape(self, text):
        def fixup(m):
            text = m.group(0)
            code = m.group(1)
            try:
                codepoint = None
                if text[1] == u'#':  # character reference
                    if text[2] == u'x':
                        codepoint = int(code[1:], 16)
                    else:
                        codepoint = int(code)
                else:               # named entity
                    codepoint = name2codepoint[code]
                if sys.version_info.major == 2:
                    return unichr(codepoint)
                else:
                    return chr(codepoint)
            except:
                return text # leave as is

        return re.sub(u'&#?(\w+);', fixup, text)

    def _DropSpans(self, matches, text):
        """Drop from text the blocks identified in matches"""
        matches.sort()
        res = u''
        start = 0
        for s, e in  matches:
            res += text[start:s]
            start = e
        res += text[start:]
        return res
