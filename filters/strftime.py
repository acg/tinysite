#!/usr/bin/env python3

import time
import datetime

def strftime(t,format):
  if isinstance(t,datetime.datetime):
    return t.strftime(format)
  elif isinstance(t,str):
    t = datetime.datetime.strptime(t,"%Y-%m-%dT%H:%M:%S-0000")
    return t.strftime(format)
  else:
    return time.strftime(format,t)

