#!/usr/bin/env python

import jinja2
import pkglist
import templating.plugins
import templating.filters
import os
from os.path import normpath, relpath, splitext


class Templater( object ):

  def __init__( self, template_includes=None, template_globals=None ):

    if template_includes == None:
      template_includes = []
    if template_globals == None:
      template_globals = {}

    self.template_includes = template_includes
    self.template_globals = template_globals

    # Dynamically load all the templating plugins.

    plugins = {}
    for module, modname in pkglist.iter_package_modules(templating.plugins):
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

    filters = {}
    for module, modname in pkglist.iter_package_modules(templating.filters):
      if hasattr(module,'FILTER'):
        filters[modname] = module.FILTER
      else:
        for name in dir(module):
          o = getattr(module,name)
          if callable(o):
            filters[name] = o

    self.filters = filters


  def get_template( self, template, other_globals=None ):

    # Allow template paths that are absolute, or that are relative to the
    # current working directory, so long as they can be resolved to a
    # path relative to one of the allowed template inclusion directories.

    for incdir in self.template_includes:
      p = relpath(abspath(template), start=abspath(incdir))
      if not p.startswith('/') and not p.startswith('../'):
        template = p
        break

    ext = splitext(template)[1]

    # Set up and create a template object.

    jinja_loader = jinja2.FileSystemLoader( self.template_includes )
    jinja_env = RelativeEnvironment( loader=jinja_loader, autoescape=(ext in ('.html','.xml')), extensions=['jinja2.ext.autoescape'] )
    jinja_env.filters.update( self.filters )
    jinja_env.globals.update( plugins=self.plugins )
    jinja_env.globals.update( self.template_globals )
    jinja_env.globals.update( other_globals if other_globals else {} )
    jinja_template = jinja_env.get_template( template )

    return jinja_template


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


