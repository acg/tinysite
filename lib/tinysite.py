#!/usr/bin/env python

import sys
import io
import os
import re
import time
import errno
import codecs
import optparse
from os.path import normpath, relpath, dirname, splitext
import pkgutil
import jinja2
import jinja2.meta
from jinja2.exceptions import TemplateNotFound
from http_parser.http import HttpStream, HTTP_REQUEST
from http_parser.util import status_reasons
try:
  from sendfile import sendfile
except:
  sendfile = None
from mimetypes import guess_type
import simplejson as json
import markdown
import pygments
import pygments.lexers
import pygments.formatters


def main( argv, stdin, stdout, stderr ):

  prog = argv[0].split('/')[-1]
  optp = optparse.OptionParser()
  optp.add_option( '-t', '--template-root', help="Path to templates directory.", default=os.environ.get('TEMPLATE_ROOT',"templates"))
  optp.add_option( '-c', '--content-root', help="Path to content directory.", default=os.environ.get('CONTENT_ROOT',"content"))
  optp.add_option( '-s', '--static-root', help="Path to static content directory.", default=os.environ.get('STATIC_ROOT',"static"))
  optp.add_option( '-T', '--template', help="Explicitly set template to use.")
  opts, args = optp.parse_args( args=argv[1:] )

  config = Record()
  config.update(vars(opts).items())

  command = args.pop(0) if len(args) else None

  if command == 'render':
    print >> stdout, render( config, args.pop(0) )
    ok = True
  elif command == 'scan':
    for srcpath, dstpath in scan( config, args.pop(0) ):
      print "%s : %s\n\n" % (srcpath,dstpath),
    ok = True
  elif command == 'httpd':
    ok = http_serve( config, stdin, stdout )
  else:
    print >> stderr, "unknown command"
    ok = False

  return 0 if ok else 100


# Core functionality.

def render( config, path ):

  path = resolve_path( path )

  # Look for content at same path, but with markdown extension, /foo/bar.html => /foo/bar.html.md
  content_path = path+'.md'

  # Load the template.
  templater = Templater([ config.template_root ])
  template = templater.get_template( config.template or path )

  # Load the content
  data, content = load_content( config.content_root+'/'+content_path )
  data['content'] = content
  data['uri'] = path

  # Render and output the template.
  output = template.render( **data ).encode('utf-8')
  return output


def resolve_path( path ):

  # Sanitize request path: don't let it escape the root.
  original_path, path = path, normpath( path.lstrip('/') )
  if path.startswith('../'):
    raise InvalidRequestPath("invalid request path: %s" % original_path)
  elif path == '.':
    path = ''
  path = '/'+path
  if original_path.endswith('/') and path != '/':
    path = path+'/'

  # Turn trailing slash into .html, eg /foo/bar/ => /foo/bar.html
  # Also turn extensionless urls into .html, eg /foo/bar-baz => /foo/bar-baz.html
  if path == '/':
    path = '/index.html'
  elif path.endswith('/') or path.split('/')[-1].find('.') < 0:
    path = path.rstrip('/')+'.html'

  return path


def load_content( content_path, expand=True ):
  in_header = False
  data = ''
  content = ''
  with codecs.open(content_path,'r','utf-8') as f:
    for linenum, line in enumerate(f):
      # Skip an initial blank line.
      if linenum == 0 and line == '\n':
        continue
      # Recognize JSON data header.
      if linenum == 1 and line == '    {\n':
        in_header = True
      elif in_header and line == '\n':
        in_header = False
      # Accumulate data or content.
      if in_header:
        data += line
      else:
        content += line
  data = json.loads(data) if data else {}
  data = expand_data( data, content_path ) if expand else data
  return data, content


def expand_data( data, filepath ):

  cwd = dirname(filepath)

  def expand_visitor( data, datapath ):

    if not len(datapath): return
    if not datapath[-1] in ['#include','#load','#extend']: return

    directive = datapath[-1]
    incdata = {}

    for relpath in [ "%s/%s" % (cwd,incpath) for incpath in data ]:
      if relpath.endswith('.json'):
        with file(relpath) as f:
          d = json.load(f)
        if directive != '#load':
          expand_data( d, relpath )
      else:
        with file(relpath) as f:
          d = f.read()
      incdata = dmerge( incdata, d )

    if directive == '#include' or directive == '#load':
      return DOP( op='update',  key=datapath[-1], val=incdata )
    elif directive == '#extend':
      return DOP( op='prepend', key=datapath[-1], val=incdata )

  def expand_orderer( a, b ):
    # When walking dictionaries, we need to encounter #extend directives first.
    return -(cmp(a=='#extend',b=='#extend')) or cmp(a,b)

  return dwalk( data, expand_visitor, expand_orderer )


def scan_data( data, filepath, dependencies=None, scanned=None, recurse=True ):

  dependencies = dependencies or []
  scanned = scanned or set()
  filepath = normpath(filepath)
  scanned.add(filepath)
  cwd = dirname(filepath)

  def scan_visitor( data, datapath ):
    if not len(datapath): return
    if not datapath[-1] in ['#include','#load','#extend']: return
    directive = datapath[-1]

    for relpath in [ normpath("%s/%s" % (cwd,incpath)) for incpath in data ]:
      dependencies.append( (filepath,relpath,) )
      if relpath in scanned: continue
      if not recurse: continue
      if relpath.endswith('.json') and directive != '#load':
        with file(relpath) as f:
          d = json.load(f)
          scan_data( d, relpath, dependencies, scanned, recurse )

  dwalk( data, scan_visitor )
  return dependencies


# File dependency scanning.

def scan( config, path ):

  original_path = path

  if path.startswith( config.static_root ):

    # /static path. Compute transitive dependencies contributed by the content and the template.

    path = path[len(config.static_root):]
    transitive = True
    scan_content = True
    scan_template = True

  elif path.startswith( config.content_root ):

    # /content path. Compute all content dependencies starting at this content file.

    path = path[len(config.content_root):]
    transitive = False
    scan_content = True
    scan_template = False

  elif path.startswith( config.template_root ):

    # /templates path. Compute all template dependencies starting at this template file.

    path = path[len(config.template_root):]
    transitive = False
    scan_content = False
    scan_template = True

  else:

    return []

  # Reconstruct paths

  static_path   = config.static_root + path
  content_path  = config.content_root + path + '.md'
  template_path = config.template_root + path
  dependencies = []

  # Scan for content dependencies.

  if scan_content:
    data, content = load_content( content_path, expand=False )
    dependencies += scan_data( data, content_path )

  # Scan for template dependencies.

  if scan_template:
    templater = Templater([ config.template_root ])
    dependencies += templater.scan_template( template_path )

  # In transitive mode, report all transitive dependencies as
  # direct dependencies of the original file.

  if transitive:
    return [ (original_path,dstpath) for srcpath,dstpath in dependencies ]
  else:
    return dependencies


# HTTP handling.

def http_serve( config, stdin, stdout ):

  # Re-open the stdin and stdout file descriptors using raw unbuffered i/o.
  stdin = io.FileIO( stdin.fileno() )
  stdout = io.FileIO( stdout.fileno(), 'w' )

  # Parse an HTTP request on stdin.
  parser = HttpStream( stdin, kind=HTTP_REQUEST )
  wsgi_env = parser.wsgi_environ()
  request_method = wsgi_env['REQUEST_METHOD']
  request_path = wsgi_env['PATH_INFO']
  request_length = wsgi_env.get('HTTP_CONTENT_LENGTH',0)
  request_body = parser.body_file()

  try:

    success = False

    if request_method != 'GET':
      raise HttpError(405)

    if request_path.endswith('/'):
      http_respond( stdout, 301, location=request_path.rstrip('/'), body='' )
    else:
      path = resolve_path(request_path)
      mimetype = guess_type(path)[0]

      try:
        output = render( config, request_path )
        http_respond( stdout, 200, mimetype=mimetype, body=output )
      except TemplateNotFound as e:
        # Retry as static file.
        full_static_path = config.static_root + path
        with file( full_static_path ) as static_file:
          http_respond( stdout, 200, mimetype=mimetype, body=static_file )

    success = True

  except InvalidRequestPath as e:
    http_respond(stdout, 400)
  except HttpError as e:
    http_respond(stdout, e.status)
  except IOError as e:
    if e.errno == errno.ENOENT:
      http_respond(stdout, 404)
    elif e.errno == errno.EACCES:
      http_respond(stdout, 403)
    else:
      http_respond(stdout, 500)
  except:
    http_respond(stdout, 500)

  return success


def http_respond( out, status, reason=None, version="HTTP/1.0", body=None, length=None, mimetype='text/html', location=None ):
  # TODO prevent headers from being emitted a second time

  reason = reason or status_reasons[status]

  # Basic http error page.
  if body == None and status >= 400:
    body = "<html><body><h1>%d %s</h1></body></html>" % (status, reason)

  # Calculate content length from body.
  if length == None:
    if isinstance(body,basestring):
      length = len(body)
    elif isinstance(body,file):
      stat = os.fstat(body.fileno())
      length = stat.st_size

  # Output http headers.
  print >> out, "%s %s %s\r\n" % (version, status, reason),
  print >> out, "Content-Length: %d\r\n" % (length),
  print >> out, "Content-Type: %s\r\n" % (mimetype),
  print >> out, "Connection: close\r\n",
  print >> out, "Date: %s\r\n" % time.strftime("%a, %d %b %Y %T %z"),
  if location: print >> out, "Location: %s\r\n" % location,
  print >> out, "\r\n",

  # Output http body, if we have one.
  if isinstance(body,basestring):
    print >> out, body,
  elif isinstance(body,file):
    rfd = body.fileno()
    wfd = out.fileno()
    offset = 0
    while length > 0:
      if sendfile:
        sent = sendfile( wfd, rfd, offset, length )
      else:
        chunk = os.read( rfd, min(length, 4096) )
        sent = os.write( wfd, chunk )
      if sent == 0: break
      offset += sent
      length -= sent

  return


# Templating.

class Templater( object ):

  def __init__( self, template_includes=None, template_globals=None ):

    if template_includes == None:
      template_includes = []
    if template_globals == None:
      template_globals = {}

    self.template_includes = template_includes
    self.template_globals = template_globals

    # Dynamically load all the templating plugins.

    try:
      import plugins as plugins_package
    except ImportError as e:
      plugins_package = None

    plugins = {}
    for module, modname in iter_package_modules(plugins_package) if plugins_package else []:
      if hasattr(module,'PLUGIN'):
        plugins[modname] = module.PLUGIN
      else:
        plugins[modname] = {}
        for name in dir(module):
          o = getattr(module,name)
          if callable(o):
            plugins[modname][name] = o

    self.plugins = plugins

    # Dynamically load all the templating filters.

    try:
      import filters as filters_package
    except ImportError as e:
      filters_package = None

    filters = { 'markdown': filter_markdown }
    for module, modname in iter_package_modules(filters_package) if filters_package else []:
      if hasattr(module,'FILTER'):
        filters[modname] = module.FILTER
      else:
        for name in dir(module):
          o = getattr(module,name)
          if callable(o):
            filters[name] = o

    self.filters = filters


  def get_template( self, template, other_globals=None ):

    templatedir, template = self.resolve_template( template )
    ext = splitext(template)[1]

    # Set up and create a template object.

    jinja_env = self.get_environment( autoescape=(ext in ('.html','.xml')), extensions=['jinja2.ext.autoescape'], other_globals=other_globals )
    jinja_template = jinja_env.get_template( template )

    return jinja_template


  def scan_template( self, template, dependencies=None, scanned=None, recurse=True ):

    dependencies = dependencies or []
    scanned = scanned or set()
    templatedir, template = self.resolve_template( template )
    templatepath = "%s/%s" % (templatedir,template)
    scanned.add(templatepath)
    cwd = dirname(templatepath)

    jinja_env = self.get_environment()
    source = file(templatepath).read()
    jinja_ast = jinja_env.parse( source, filename=templatepath )

    for refpath in list(jinja2.meta.find_referenced_templates(jinja_ast)):
      if not refpath: continue
      refpath = normpath( "%s/%s" % (cwd,refpath) )
      dependencies.append( (templatepath,refpath), )
      if not refpath in scanned and recurse:
        self.scan_template( refpath, dependencies, scanned, recurse )

    return dependencies


  def resolve_template( self, template, extra_includes=None ):

    # Allow template paths that are absolute, or that are relative to the
    # current working directory, so long as they can be resolved to a
    # path relative to one of the allowed template inclusion directories.

    templatedir = None
    extra_includes = extra_includes or []

    for incdir in extra_includes + self.template_includes:
      p = relpath(abspath(template), start=abspath(incdir))
      if not p.startswith('/') and not p.startswith('../'):
        templatedir = incdir
        template = p
        break

    return templatedir, template


  def get_environment( self, autoescape=True, extensions=None, other_globals=None ):

    # Set up and create a jinja template environment.

    jinja_loader = jinja2.FileSystemLoader( self.template_includes )
    jinja_env = RelativeEnvironment( loader=jinja_loader, autoescape=autoescape, extensions=(extensions or []) )
    jinja_env.filters.update( self.filters )
    jinja_env.globals.update( plugins=self.plugins )
    jinja_env.globals.update( self.template_globals )
    jinja_env.globals.update( other_globals if other_globals else {} )

    return jinja_env



def filter_markdown(value):
  if not value: return value

  value = unicode(value)

  # Recognize ```lang fenced code blocks in markdown.

  re_fenced_code = re.compile(r'''
  ^
    ```(?P<language>\S+) \s*
    \n
    (?P<content>.*)
    \n
    ```
  $
  ''', re.S|re.X)

  re_fenced_code_split = re.compile(r'''
  (
    ```\S+ \s*
    \n
    .*?
    \n
    ```
  )
  ''', re.S|re.X)

  re_strikethrough = re.compile(r'(^|\s)~~([^~]+?)~~($|\s)')

  html = []

  for i, block in enumerate(re_fenced_code_split.split(value)):
    if i % 2:  # fenced code
      m = re_fenced_code.match(block)
      lexer = pygments.lexers.get_lexer_by_name(m.group('language'))
      formatter = pygments.formatters.get_formatter_by_name('html')
      html.append(pygments.highlight(m.group('content'), lexer, formatter))
    else:      # regular markdown content
      block = re.sub(re_strikethrough, r'\1<strike>\2</strike>\3', block)
      html.append(markdown.markdown(block, extensions=['toc']))

  return u''.join(html)


def abspath( path ):
  """ Unfortunately, os.path.abspath does some physical cleanup. """
  if path.startswith('/'):
    return path
  else:
    return normpath(os.environ['PWD']+'/'+path)


class RelativeEnvironment(jinja2.Environment):
  """ Override join_path() to enable relative template paths. """
  def join_path(self, template, parent):
    return normpath(os.path.join(os.path.dirname(parent), template))


def iter_package_modules( pkg ):
  for importer, modname, _ in pkgutil.iter_modules( pkg.__path__ ):
    full_package_name = "%s.%s" % ( pkg.__name__, modname )
    if full_package_name not in sys.modules:
      module = importer.find_module(modname).load_module(full_package_name)
      yield module, modname


# Operations on nested data structures.

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


# Convenience class. A dict that allows foo.bar instead of just foo["bar"].

class Record( dict ):
  def __getattr__( self, name ):
    return self[name]
  def __setattr__( self, name, value ):
    self[name] = value
    return value


# Exception types.

class InvalidRequestPath(Exception): pass

class HttpError(Exception):
  def __init__(self, status):
    self.status = status
    self.message = "HTTP Error %d" % status

