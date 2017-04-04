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

def is_allowed_title(title):
    return title not in [
            u'Blog', u'Category', u'Category talk', u'Discussion', u'File', u'File talk',
            'Forum', u'Forum talk', u'Help', u'Help talk', u'MediaWiki', u'MediaWiki talk',
            'Talk', u'Template', u'Template talk', u'User', u'User blog', u'User talk', u'User blog comment']
