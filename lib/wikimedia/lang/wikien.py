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

import locale

def is_allowed_title(title):
    return title not in ["Blog","Category","Category talk","Discussion","File","File talk",
                        "Forum","Forum talk","Help","Help talk","MediaWiki","MediaWiki talk",
                        "Talk","Template","Template talk","User","User blog","User talk","User blog comment"]
