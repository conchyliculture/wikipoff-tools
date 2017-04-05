# -*- coding: utf-8 -*-

import re
import lib.wikimedia.languages as languages
import lib.wikimedia.wikiglobals as wikiglobals
try:
    from htmlentitydefs import name2codepoint
except:
    from html.entities import name2codepoint

toomanybr = re.compile(r'<br/>(<br/>(?:<br/>)+)')


class WikimediaTranslator(object):
    def __init__(self, wiki=u'wikipedia', lang=u'en'):
        self.lang = lang
        self.wiki = wiki
        self.translator = self._SetTranslator()

    def IsAllowedTitle(self, title):
        return title not in [
            u'Blog', u'Category', u'Category talk', u'Discussion', u'File', u'File talk',
            'Forum', u'Forum talk', u'Help', u'Help talk', u'MediaWiki', u'MediaWiki talk',
            'Talk', u'Template', u'Template talk', u'User', u'User blog', u'User talk', u'User blog comment']

    def translate(self, input_text):
        return self.translator.translate(input_text)

    def _SetTranslator(self):
        if self.wiki == u'wikipedia':
            if self.lang == u'fr':
                self.translator = languages.wikifr.WikiFRTranslator()

#    def get_is_allowed_title_func(self):
#        if self.wiki == u'wikipedia':
#            if self.lang == u'fr':
#                return languages.wikifr.is_allowed_title
#
#        return languages.wikien.is_allowed_title

def WikiConvertToHTML(title, text, translator):
    buff = u''
    if translator is None:
        raise Exception(u'You asked for conversion, and gave me no translator, wtf is wrong with you')
    text = clean(text, translator)
    for line in compact(text):
        buff += line#.encode('utf-8')
    buff = toomanybr.sub(r'<br/><br/>', buff)
    buff = buff.replace(u'<math>', u'\(')
    buff = buff.replace(u'</math>', u'\)')

    return (title, buff)

##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
    def fixup(m):
        text = m.group(0)
        code = m.group(1)
        try:
            if text[1] == "#":  # character reference
                if text[2] == "x":
                    return unichr(int(code[1:], 16))
                else:
                    return unichr(int(code))
            else:               # named entity
                return unichr(name2codepoint[code])
        except:
            return text # leave as is

    return re.sub("&#?(\w+);", fixup, text)

# Match list stars
LIST_RE = re.compile(r'^\*+')

# Match HTML comments
COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)

# Match elements to ignore
DISCARD_ELEMENT_PATTERNS = []
for tag in wikiglobals.discard_elements:
    pattern = re.compile(r'<\s*%s\b[^>]*>.*?<\s*/\s*%s>' % (tag, tag), re.DOTALL | re.IGNORECASE)
    DISCARD_ELEMENT_PATTERNS.append(pattern)

# Match ignored tags
IGNORED_TAG_PATTERNS = []
def IgnoreTag(tag):
    left = re.compile(r'<\s*%s\b[^>]*>' % tag, re.IGNORECASE)
    right = re.compile(r'<\s*/\s*%s>' % tag, re.IGNORECASE)
    IGNORED_TAG_PATTERNS.append((left, right))

for tag in wikiglobals.ignored_tags:
    IgnoreTag(tag)

# Match selfClosing HTML tags
selfClosing_tag_patterns = []
for tag in wikiglobals.self_closing_tags:
    pattern = re.compile(r'<\s*%s\b[^/]*/\s*>' % tag, re.DOTALL | re.IGNORECASE)
    selfClosing_tag_patterns.append(pattern)

# Match HTML placeholder tags
placeholder_tag_patterns = []
for tag, repl in wikiglobals.placeholder_tags.items():
    pattern = re.compile(
        r'<\s*%s(\s*| [^>]+?)>.*?<\s*/\s*%s\s*>' % (tag, tag),
        re.DOTALL | re.IGNORECASE)
    placeholder_tag_patterns.append((pattern, repl))

# Match preformatted lines
preformatted = re.compile(r'^ .*?$', re.MULTILINE)

# Match external links (space separates second optional parameter)
EXTERNAL_LINK_RE = re.compile(r'\[\w+.*? (.*?)\]')
EXTERNAL_LINK_NO_ANCHOR_RE = re.compile(r'\[\w+[&\]]*\]')

# Matches bold/italic
bold_italic = re.compile(r"'''''([^']*?)'''''")
bold = re.compile(r"'''(.*?)'''")
italic_quote = re.compile(r"''\"(.*?)\"''")
italic = re.compile(r"''([^']*)''")
quote_quote = re.compile(r'""(.*?)""')

# Matches space
spaces = re.compile(r' {2,}')

# Matches dots
dots = re.compile(r'\.{4,}')

# A matching function for nested expressions, e.g. namespaces and tables.
def dropNested(text, openDelim, closeDelim):
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
    res = ''
    start = 0
    for s, e in  matches:
        res += text[start:s]
        start = e
    res += text[start:]
    return res

def dropSpans(matches, text):
    """Drop from text the blocks identified in matches"""
    matches.sort()
    res = ''
    start = 0
    for s, e in  matches:
        res += text[start:s]
        start = e
    res += text[start:]
    return res

# Match interwiki links, | separates parameters.
# First parameter is displayed, also trailing concatenated text included
# in display, e.g. s for plural).
#
# Can be nested [[File:..|..[[..]]..|..]], [[Category:...]], etc.
# We first expand inner ones, than remove enclosing ones.
#
WIKI_LINK_RE = re.compile(r'\[\[([^[]*?)(?:\|([^[]*?))?\]\](\w*)')

PARAMETRIZED_RE = re.compile(r'\[\[.*?\]\]')

# Function applied to wikiLinks
def make_anchor_tag(match):
    link = match.group(1)
    #colon = link.find(':')
    trail = match.group(3)
    anchor = match.group(2)
    if not anchor:
        anchor = link
    anchor += trail
    if wikiglobals.keep_links:
        return '<a href="%s">%s</a>' % (link, anchor)
    else:
        return anchor

def clean(text, translator):

    text = translator.translate(text)

    # FIXME: templates should be expanded
    # Drop transclusions (template, parser functions)
    # See: http://www.mediawiki.org/wiki/Help:Templates
    text = dropNested(text, r'{{', r'}}')

    # Drop tables
    text = dropNested(text, r'{\|', r'\|}')

    # Expand links
    text = WIKI_LINK_RE.sub(make_anchor_tag, text)
    # Drop all remaining ones
    text = PARAMETRIZED_RE.sub('', text)

    # Handle external links
    text = EXTERNAL_LINK_RE.sub(r'\1', text)
    text = EXTERNAL_LINK_NO_ANCHOR_RE.sub('', text)

    # Handle bold/italic/quote
    text = bold_italic.sub(r'<i>\1</i>', text)
    text = bold.sub(r'<b>\1</b>', text)
    text = italic_quote.sub(r'&quot;\1&quot;', text)
    text = italic.sub(r'&quot;\1&quot;', text)
    text = quote_quote.sub(r'\1', text)
    text = text.replace("'''", '').replace("''", '&quot;')

    ################ Process HTML ###############

    # turn into HTML
    text = unescape(text)
    # do it again (&amp;nbsp;)
    text = unescape(text)

    # Collect spans

    matches = []
    # Drop HTML comments
    for m in COMMENT_RE.finditer(text):
        matches.append((m.start(), m.end()))

    # Drop self-closing tags
    for pattern in selfClosing_tag_patterns:
        for m in pattern.finditer(text):
            matches.append((m.start(), m.end()))

    # Drop ignored tags
    for left, right in IGNORED_TAG_PATTERNS:
        for m in left.finditer(text):
            matches.append((m.start(), m.end()))
        for m in right.finditer(text):
            matches.append((m.start(), m.end()))

    # Bulk remove all spans
    text = dropSpans(matches, text)

    # Cannot use dropSpan on these since they may be nested
    # Drop discarded elements
    for pattern in DISCARD_ELEMENT_PATTERNS:
        text = pattern.sub(u'', text)

    # Expand placeholders
    for pattern, placeholder in placeholder_tag_patterns:
        index = 1
        for match in pattern.finditer(text):
            text = text.replace(match.group(), u'%s_%d' % (placeholder, index))
            index += 1

    text = text.replace(u'<<', u'Â«').replace(u'>>', u'Â»')

    #############################################

    # Drop preformatted
    # This can't be done before since it may remove tags
    text = preformatted.sub(u'', text)

    # Cleanup text
    text = text.replace(u'\t', u' ')
    text = spaces.sub(u' ', text)
    text = dots.sub(u'...', text)
    text = re.sub(u' (,:\.\)\]Â»)', r'\1', text)
    text = re.sub(u'(\[\(Â«) ', r'\1', text)
    text = re.sub(r'\n\W+?\n', '\n', text) # lines with only punctuations
    text = text.replace(u',,', u',').replace(u',.', u'.')
    return text

section = re.compile(r'(==+)\s*(.*?)\s*\1')

def compact(text):
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
        m = section.match(line)
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
                    listdepth = len(LIST_RE.search(line).group())
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

def handle_unicode(entity):
    numeric_code = int(entity[2:-1])
    if numeric_code >= 0x10000:
        return u''
    return unichr(numeric_code)

#------------------------------------------------------------------------------
