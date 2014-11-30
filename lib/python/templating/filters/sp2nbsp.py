#!/usr/bin/env python

import re

def sp2nbsp(value):
  if not value: return value
  return unicode(value).replace('  ','&nbsp;')

