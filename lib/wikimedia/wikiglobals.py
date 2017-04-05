##
# Whether to preseve links in output
#
keep_links = True

# handle 'a' separetely, depending on keep_links
ignored_tags = [
    u'big', u'blockquote', u'center', u'cite', u'div', u'em',
    u'font', u'h1', u'h2', u'h3', u'h4', u'hiero', u'kbd', u'nowiki',
    u's', u'tt', u'var',
]

# This is obtained from the dump itself
prefix = None # Lost?

##
# Whether to transform sections into HTML
#
keep_sections = True

##
# Drop these elements from article text
#
discard_elements = set([
    u'gallery', u'timeline', u'noinclude', u'pre',
    u'table', u'tr', u'td', u'th', u'caption',
    u'form', u'input', u'select', u'option', u'textarea',
    u'ul', u'li', u'ol', u'dl', u'dt', u'dd', u'menu', u'dir',
    u'ref', u'references', u'img', u'imagemap', u'source'
])

self_closing_tags = [u'br', u'hr', u'nobr', u'ref', u'references']

placeholder_tags = {u'code': u'codice'}
