SHELL = /usr/bin/env bash


all : compiled-python

compiled-python : remove-stale-pyc
	python3 -m compileall -j 0 lib

remove-stale-pyc : remove-stale-py2-pyc remove-stale-py3-pyc

remove-stale-py2-pyc : force
	find lib -name \*.pyc -a -not -path "*/__pycache__/*" | xargs --no-run-if-empty rm -v

remove-stale-py3-pyc : force
	find lib -path "*/__pycache__/*.pyc" | while read cfile; do sfile="$$cfile"; sfile="$${sfile/__pycache__?/}"; sfile="$${sfile%%.cpython-*.pyc}.py"; test -e "$$sfile" || echo "$$cfile"; done | xargs --no-run-if-empty rm -v


.PHONY : force

### Delete $@ if a rule fails. GNU make-specific.
.DELETE_ON_ERROR :

