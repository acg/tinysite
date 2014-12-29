# tinysite

tinysite is a static site generator.

## Requirements

0. Content is authored in markdown and separated from presentation.
0. Templates are user-controlled, extensible via plugins/filters, and authored in a standard template language (jinja2).
0. Incremental site rebuilds are fast, correct, and use a standard build tool (make).
0. Content files can contain a data section in a standard data format (json).
0. Data sections can include external data via file inclusion.
0. Pages which aggregate content + data from multiple other pages are possible (eg blog home page, archives).
0. There's a dynamic http server that makes your edit-preview loop fast.
0. Minification and asset compilation are possible and use the same standard build tool.
0. Dependencies are minimal. You can rebuild your site on a resource-constrained box.

## Comparison

- Jekyll lacks incremental site regeneration and slows your edit-preview loop to a crawl. So you fixed a small typo on one page? Time to rebuild the whole site! There's a [3-year-old github issue](https://github.com/jekyll/jekyll/issues/380) tracking this. The planned solution is to reinvent a build tool inside of jekyll.
- Jekyll has a built-in *static* http server. You can tell it to watch for filesystem changes and kick off full rebuilds.

## Requirements

- `GNU make` - for build
- `python 2.6+`
- `markdown.py` - for content
- `jinja2` - for templating
- `simplejson` - for data
- `http_parser.py` - for local server
- `ucspi-tcp` - for local server

