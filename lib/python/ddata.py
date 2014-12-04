#!/usr/bin/env python


def dmerge( d1, d2, **opts ):

  if isinstance(d1,dict) and isinstance(d2,dict):

    d3 = dict(d1.items())
    for k,v in d2.items():
      d3[k] = dmerge(d3.get(k,None),v,**opts)

  elif isinstance(d1,list) and isinstance(d2,list):

    list_strategy = opts.get('list_strategy','append')

    if list_strategy == 'append':
      d3 = d1[:] + d2[:]
    elif list_strategy == 'prepend':
      d3 = d2[:] + d1[:]
    else:
      d3 = [None] * max(len(d1),len(d2))
      for i in xrange(0,len(d3)):
        if i < len(d1) and i < len(d2):
          d3[i] = dmerge(d1[i],d2[i],**opts) if list_strategy == 'merge' else d2[i]
        elif i < len(d1):
          d3[i] = d1[i]
        else:
          d3[i] = d2[i]

  elif d2 == None:
    return d1

  else:
    return d2

  return d3


def dset( data, path, value, delim="." ):
  if isinstance(path,basestring):
    path = path.split(delim)
  if len(path) == 0:
    return data
  elif len(path) == 1:
    if isinstance(data,list):
      index = int(path[0])
      pad = index - len(data) + 1
      if pad > 0: data[index:] = [None] * pad
      data[index] = value
    else:
      data[path[0]] = value
    return data
  else:
    wantlist = False
    if path[0].startswith('[') and path[0].endswith(']'):
      path[0] = path[0][1:-1]
      wantlist = True
    atpath = data.get(path[0],None)
    if not isinstance(atpath,(dict,list,)):
      if wantlist:
        data[path[0]] = []
      else:
        data[path[0]] = {}
    return dset( data[path[0]], path[1:], value )


def dwalk( data, visitor, orderer=None, path=None ):

  if not orderer:
    orderer = lambda a,b: cmp(a,b)
  if not path:
    path = []

  result = visitor( data, path ) or DOP(op=None)

  if not result.op:
    if isinstance(data,dict):
      d = dwalk_dict( data, visitor, orderer, path )
      data.clear()
      data.update(d)
    elif isinstance(data,list):
      data[:] = dwalk_list( data, visitor, orderer, path )

  if len(path):
    return result
  else:
    return data


def dwalk_dict( data, visitor, orderer, path ):

  d = {}

  for k in sorted( data.keys(), cmp=orderer ):
    v = data[k]
    r = dwalk( v, visitor, orderer, path+[k] ) or DOP(op=None)

    if r.op == 'delete':
      pass
    elif r.op == 'update':
      d[r.key] = r.val
    elif r.op == 'prepend':
      d = dmerge( r.val, d )
    elif r.op == 'append':
      d = dmerge( d, r.val )
    else:
      d[k] = v

  return d


def dwalk_list( data, visitor, orderer, path ):

  d = []

  for i in xrange(len(data)):
    v = data[i]
    r = dwalk( v, visitor, orderer, path+[i] ) or DOP(op=None)

    if r.op == 'delete':
      pass
    elif r.op == 'update':
      d = d + [r.val]
    elif r.op == 'prepend':
      d = r.val + d
    elif r.op == 'append':
      d = d + r.val
    else:
      d = d + [v]

  return d


class DOP( object ):
  def __init__( self, op=None, key=None, val=None ):
    self.op = op
    self.key = key
    self.val = val


