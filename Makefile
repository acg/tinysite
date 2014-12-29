TINYSITE_ROOT ?= $(CURDIR)

### Custom shell for all rules in this Makefile.
SHELL = bash -o pipefail -c

CONTENT_ROOT  ?= content
STATIC_ROOT   ?= static
TEMPLATE_ROOT ?= templates
BUILD_ROOT    ?= build

export CONTENT_ROOT
export STATIC_ROOT
export TEMPLATE_ROOT
export BUILD_ROOT

REMOTE_USER   ?=
REMOTE_HOST   ?=
REMOTE_DIR    ?=

LISTEN_HOST    ?= 127.0.0.1
LISTEN_PORT    ?= 8484

CONTENT_FILES = $(shell find ${CONTENT_ROOT} -type f -a -name \*.md -a -not -path "*/_*/*" | sort)
PAGES         = $(CONTENT_FILES:${CONTENT_ROOT}/%.md=${STATIC_ROOT}/%.html)
DEPS          = $(CONTENT_FILES:${CONTENT_ROOT}/%.md=${BUILD_ROOT}/%.html.d)

### For build rule highlighting.

COLOR_BUILD = \e[36m
COLOR_SCAN  = \e[35m
COLOR_RESET = \e[0m


all : pages

pages : $(PAGES)

$(STATIC_ROOT)/%.html : $(TEMPLATE_ROOT)/%.html $(CONTENT_ROOT)/%.md
	@ mkdir -p `dirname "$@"`
	@   test -t 1 && printf "$(COLOR_BUILD)" || true
	@   printf "[render]"
	@   test -t 1 && printf "$(COLOR_RESET)" || true
	@   printf " %s\n" "$(@:${STATIC_ROOT}%.html=%)"
	@ tinysite render "$(@:${STATIC_ROOT}%=%)" > "$@"

serve : force
	@ printf "server running on %s\n" "http://$(LISTEN_HOST):$(LISTEN_PORT)/"
	@ tcpserver -v "$(LISTEN_HOST)" "$(LISTEN_PORT)" tinysite httpd

sync : force
	rsync -avzp --exclude ".*" "$(OUT)/" "$(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)/"

clean :
	@ rm -vf $(PAGES) $(DEPS)


### Scan templates and content+data for file dependencies.
### Ensures correct incremental builds.

deps : $(DEPS)

$(BUILD_ROOT)/%.html.d : $(TEMPLATE_ROOT)/%.html $(CONTENT_ROOT)/%.md
	@ mkdir -p `dirname "$@"`
	@   test -t 1 && printf "$(COLOR_SCAN)" || true
	@   printf "[scan]"
	@   test -t 1 && printf "$(COLOR_RESET)" || true
	@   printf " %s\n" "$(@:${BUILD_ROOT}/%.html.d=/%)"
	@ tinysite scan "$(@:${BUILD_ROOT}/%.d=${STATIC_ROOT}/%)" | sed -nEe "p; s@^${STATIC_ROOT}(.+?) :@\n${BUILD_ROOT}\1.d :@p;" > "$@"

ifeq (, $(findstring $(MAKECMDGOALS), clean ))
  -include $(DEPS)
endif



.PHONY : force

### Delete $@ if a rule fails. GNU make-specific.
.DELETE_ON_ERROR :

