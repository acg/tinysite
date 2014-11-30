#!/usr/bin/env python

from __future__ import absolute_import
from markdown import Markdown

def markdown(value):
  if not value: return value
  md = Markdown()
  return md.convert(unicode(value))

