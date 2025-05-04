#!/usr/bin/env python3

import re

def nl2br(value):
  if not value: return value
  return str(value).replace('\n','<br/>')

