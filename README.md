# tinysite

tinysite is a static site generator.

## Requirements

0. Content is authored in markdown and separated from presentation.
0. Templates are user-controlled, extensible, and authored in a standard template language.
0. Incremental site rebuilds are fast and correct.
0. Content files can be prefaced with a data section, which again uses a standard format.
0. Data sections can include external data via file inclusion.
0. Pages which aggregate content + data from multiple other pages are possible.
0. There's a development-mode server that makes the code-test loop fast.
0. Minification and asset compilation are possible, and also use a sane build system.
0. Dependencies are minimal.

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
  - In cli mode, we exercise the same flask route, but just write the response (minus HTTP headers) to stdout.
- Basic makefile which does: `templates/foo.html + content/foo.md => static/foo.html`
- Clean up bin/templatize code.
  - Move into a library.
  - Use JSON for data header format instead of "Key: Value".
  - Make the JSON construct inclusion system more sane.
- Need an inclusion scanner which generates the `*.d` files.

