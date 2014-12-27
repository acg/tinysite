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

## Development Notes

Dependencies:

- python
- markdown - for content
- jinja2 - for templating
- simplejson - for data

Code to write...

- How to write the simple dev-mode server?
  - A simple http server with a catch-all route for everything.
  - If we get a request for /foo/bar/:
    - See if content/foo/bar.md exists.
      - Yes: invoke template rendering code and return a response.
      - No: fallback to a static sendfile call.
  - In cli mode, we exercise the same route code, but just write the response (minus HTTP headers) to stdout.
- Basic makefile which does: `templates/foo.html + content/foo.md => static/foo.html`
- Clean up bin/templatize code.
  - Move into a library.
  - Use JSON for data header format instead of "Key: Value".
  - Make the JSON construct inclusion system more sane.
- Need an inclusion scanner which generates the `*.d` files.
  - Scanner for templates: use `jinja2.meta.find_referenced_templates`
  x Scanner for content: refactor `expand_visitor` so it can be used in scanner mode. No need to load data from #load directives. For #include and #extend, need to load and recurse, but don't need to keep the loaded result.
- Verify that #include, #load, and #extend all work properly.

