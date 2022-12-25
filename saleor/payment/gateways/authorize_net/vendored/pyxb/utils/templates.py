# -*- coding: utf-8 -*-
# Copyright 2009-2013, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Functions that aid with generating text from templates and maps."""

import re

# POSIX shell variable syntax:
#  Expansions with unset var
#  ${var}=
#  ${var+WORD}=
#  ${var:+WORD}=
#  ${var-WORD}=WORD
#  ${var:-WORD}=WORD
#  Expansions with empty var
#  ${var}=
#  ${var+WORD}=WORD
#  ${var:+WORD}=
#  ${var-WORD}=
#  ${var:-WORD}=WORD
#  Expansions with var=SET
#  ${var}=SET
#  ${var+WORD}=WORD
#  ${var:+WORD}=WORD
#  ${var-WORD}=SET
#  ${var:-WORD}=SET

# This expression replaces markers in template text with the value
# obtained by looking up the marker in a dictionary.
# %{id} = value
_substIdPattern = re.compile("%{(?P<id>\w+)}")

# This expression performs conditional substitution: if the expression
# provided evaluates to true in a given context, then one value is
# substituted, otherwise the alternative value is substituted.
# %{?<cond>??<true>?:<false>?}
# %{?1 == 2??true?:false?}
_substConditionalPattern = re.compile("%{\?(?P<expr>.+?)\?\?(?P<true>.*?)(\?:(?P<false>.*?))?\?}", re.MULTILINE + re.DOTALL)

# This expression tests whether an identifier is defined to a non-None
# value in the context; if so, it replaces the marker with template
# text.  In that replacement text, the value ?@ is replaced by the
# test expression.  Contrast POSIX shell ${ID+subst}${ID-subst}
# Note: NOT by the value of the test expression.  If no replacement
# text is given, the replacement '%{?@}' is used, which replaces it
# with the value of the test expression.
# %{?<id>?+<yessubst>?-?<nosubst>}}
# %{?maybe_text?+?@ is defined to be %{?@}?}
_substIfDefinedPattern = re.compile("%{\?(?P<id>\w+)(\?\+(?P<repl>.*?))?(\?\-(?P<ndrepl>.*?))?\?}", re.MULTILINE + re.DOTALL)

# The pattern which, if present in the body of a IfDefined block, is
# replaced by the test expression.
_substDefinedBodyPattern = re.compile("\?@")

def _bodyIfDefinedPattern (match_object, dictionary):
    global _substDefinedBodyPattern
    id = match_object.group('id')
    repl = match_object.group('repl')
    ndrepl = match_object.group('ndrepl')
    value = dictionary.get(id)
    if value is not None:
        if repl:
            return _substDefinedBodyPattern.sub(id, repl)
        if ndrepl:
            return ''
        return _substDefinedBodyPattern.sub(id, '%{?@}')
    else:
        if ndrepl:
            return _substDefinedBodyPattern.sub(id, ndrepl)
        return ''

def _bodyConditionalPattern (match_object, dictionary):
    global _substDefinedBodyPattern
    expr = match_object.group('expr')
    true = match_object.group('true')
    false = match_object.group('false')
    value = None
    try:
        value = eval(expr, dictionary)
    except Exception as e:
        return '%%{EXCEPTION: %s}' % (e,)
    if value:
        return _substDefinedBodyPattern.sub(expr, true)
    if false is not None:
        return _substDefinedBodyPattern.sub(expr, false)
    return ''

def replaceInText (text, **dictionary):
    global _substIfDefinedPattern
    global _substConditionalPattern
    global _substIdPattern
    global _substDefinedBodyPattern
    rv = text
    rv = _substIfDefinedPattern.sub(lambda _x: _bodyIfDefinedPattern(_x, dictionary), rv)
    rv = _substConditionalPattern.sub(lambda _x: _bodyConditionalPattern(_x, dictionary), rv)
    rv =  _substIdPattern.sub(
        lambda _x,_map=dictionary:
           _map.get(_x.group('id'), '%%{MISSING:%s}' % (_x.group('id'),))
        , rv)
    return rv
