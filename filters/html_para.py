#!/usr/bin/env python

import re

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

def html_para(value):
  """
    Turn text into html paragraphs with explicit html line breaks.
    Adapted from: http://jinja.pocoo.org/docs/api/#custom-filters
    This version assumes autoescape is enabled.
  """
  if not value: return value
  para = _paragraph_re.split(unicode(value))
  result = u'\n\n'.join(u'<p>%s</p>' % p.replace(u'\n', u'<br/>\n') for p in para)
  return result

