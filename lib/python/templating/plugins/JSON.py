#!/usr/bin/env python

import simplejson as json


def encode(data,**kwargs):
  kwargs['sort_keys'] = kwargs.get('sort_keys',True)
  kwargs['indent']    = kwargs.get('indent','  ')
  if kwargs.pop('skipvalues',False):
    kwargs['default'] = kwargs.get('default',lambda o: None)
  return json.dumps(data,**kwargs)


def decode(string,**kwargs):
  return json.loads(string,**kwargs)


def load(filename,**kwargs):
  return json.load(file(filename),**kwargs)


