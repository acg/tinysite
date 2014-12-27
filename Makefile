TINYSITE_ROOT ?= $(CURDIR)

### Custom shell for all rules in this Makefile.
SHELL = sh -c '. "$$0"/etc/main.env && exec bash -o pipefail "$$@"' "$(TINYSITE_ROOT)"

CONTENT_ROOT  ?= content
STATIC_ROOT   ?= static
TEMPLATE_ROOT ?= templates
BUILD_ROOT    ?= build

export CONTENT_ROOT
export STATIC_ROOT
export TEMPLATE_ROOT

CONTENT_FILES = $(shell find ${CONTENT_ROOT} -type f -a -name \*.md -a -not -path "*/_*/*")
PAGES         = $(CONTENT_FILES:${CONTENT_ROOT}/%.md=${STATIC_ROOT}/%.html)
DEPS          = $(CONTENT_FILES:${CONTENT_ROOT}/%.md=${BUILD_ROOT}/%.html.d)


all : pages

pages : $(PAGES)

$(STATIC_ROOT)/%.html : $(TEMPLATE_ROOT)/%.html $(CONTENT_ROOT)/%.md
	@ mkdir -p `dirname "$@"`
	tinysite render "$(@:${STATIC_ROOT}%=%)" > "$@"

sync : force
	rsync -avzp --exclude ".*" "$(OUT)/" "$(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)/"

clean :
	rm -f $(PAGES) $(DEPS)


### Scan templates and content+data for file dependencies.
### Ensures correct incremental builds.

deps : $(DEPS)

$(BUILD_ROOT)/%.html.d : $(TEMPLATE_ROOT)/%.html $(CONTENT_ROOT)/%.md
	@ mkdir -p `dirname "$@"`
	tinysite scan "$(@:${BUILD_ROOT}%.d=%)" > "$@"

ifeq (, $(findstring $(MAKECMDGOALS), clean ))
  -include $(DEPS)
endif



.PHONY : force

### Delete $@ if a rule fails. GNU make-specific.
.DELETE_ON_ERROR :

