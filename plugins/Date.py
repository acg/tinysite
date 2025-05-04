#!/usr/bin/env python3

import time
import datetime


def now(self):
  return time.time()

def strftime(self,format,t):
  if isinstance(t,datetime.datetime):
    return t.strftime(format)
  else:
    return time.strftime(format,t)

def localtime(self,t):
  return time.localtime(t)

def format_human_interval(self,t):
  units = [ ("second",60), ("minute",60), ("hour",24), ("day",365), ("year",0) ]
  for u in units:
    t = int(t)
    if t < u[1] or 0 == u[1]:
      return "%d %s%s" % (t, u[0], "" if t==1 else "s")
    t = t/float(u[1])

