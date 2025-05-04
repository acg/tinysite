#!/usr/bin/env python3

def format_human_size(self,size):
  units = [ "b","KB","MB","GB","TB" ]
  base = 1
  for u in units:
    if size < base*1024 or u == "TB":
      size = float(size) / base
      if size < 10 and size*10 - int(size)*10 >= 1:
        return "%.01f %s" % (size,u)
      else:
        return "%d %s" % (size,u)
    base *= 1024

