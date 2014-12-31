#!/usr/bin/env python

import re

def nl2br(value):
  if not value: return value
  return unicode(value).replace('\n','<br/>')

