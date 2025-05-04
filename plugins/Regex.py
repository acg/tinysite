#!/usr/bin/env python3

import re


class REGEX:

  def __init__(self, pattern, flags=0):
    self.regex = re.compile(pattern,flags)

  @staticmethod
  def __call__(*args):
    return REGEX(*args)

  def match(self, string):
    return self.regex.match(string)

  def replace(self, string, replacement):
    return self.regex.sub(replacement,string)

PLUGIN = REGEX

