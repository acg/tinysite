import pkgutil
import sys

def iter_package_modules( pkg ):
  for importer, modname, _ in pkgutil.iter_modules( pkg.__path__ ):
    full_package_name = "%s.%s" % ( pkg.__name__, modname )
    if full_package_name not in sys.modules:
      module = importer.find_module(modname).load_module(full_package_name)
      yield module, modname

