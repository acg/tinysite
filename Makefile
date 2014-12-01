TINYSITE_ROOT ?= $(CURDIR)

### Custom shell for all rules in this Makefile.
SHELL = sh -c '. "$$0"/etc/main.env && exec bash -o pipefail "$$@"' "$(TINYSITE_ROOT)"

CONTENT_ROOT  ?= content
STATIC_ROOT   ?= static
TEMPLATE_ROOT ?= templates

export CONTENT_ROOT
export STATIC_ROOT
export TEMPLATE_ROOT

CONTENT_FILES = $(shell find ${CONTENT_ROOT} -type f -a -name \*.md)
PAGES         = $(CONTENT_FILES:${CONTENT_ROOT}/%.md=${STATIC_ROOT}/%.html)


all : pages

pages : $(PAGES)

$(STATIC_ROOT)/%.html : $(TEMPLATE_ROOT)/%.html $(CONTENT_ROOT)/%.md
	@ mkdir -p `dirname "$@"`
	tinysite render "$(@:${STATIC_ROOT}%=%)" > "$@"

sync : force
	rsync -avzp --exclude ".*" "$(OUT)/" "$(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)/"

clean :
	rm -f $(PAGES)


# TODO include *.d scanner-generated dependency files here.


.PHONY : force

### Delete $@ if a rule fails. GNU make-specific.
.DELETE_ON_ERROR :

