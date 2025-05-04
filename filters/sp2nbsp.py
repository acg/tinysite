#!/usr/bin/env python3

import re

def sp2nbsp(value):
  if not value: return value
  return str(value).replace('  ','&nbsp;')

