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

CONTENT_FILES := $(shell find ${CONTENT_ROOT} -type f -a -name \*.md -a -not -path "*/_*/*" | sort)
PAGES         := $(CONTENT_FILES:${CONTENT_ROOT}/%.md=${STATIC_ROOT}/%)
DEPS          := $(CONTENT_FILES:${CONTENT_ROOT}/%.md=${BUILD_ROOT}/%.d)

### For build rule highlighting.

COLOR_BUILD := \e[36m
COLOR_SCAN  := \e[35m
COLOR_RESET := \e[0m

HIGHLIGHT_BUILD := sh -c 'test -t 1 && exec printf "$$0" "$$@" || exec printf "[%s] %s\n" "$$@"' "$(COLOR_BUILD)[%s]$(COLOR_RESET) %s\n"
HIGHLIGHT_SCAN  := sh -c 'test -t 1 && exec printf "$$0" "$$@" || exec printf "[%s] %s\n" "$$@"' "$(COLOR_SCAN)[%s]$(COLOR_RESET) %s\n"


all : pages

pages : $(PAGES)

$(STATIC_ROOT)/% : $(TEMPLATE_ROOT)/% $(CONTENT_ROOT)/%.md
	@ mkdir -p `dirname "$@"`
	@ $(HIGHLIGHT_BUILD) render "$(@:${STATIC_ROOT}%=%)"
	@ tinysite render "$(@:${STATIC_ROOT}%=%)" > "$@"

serve : force
	@ printf "server running on %s\n" "http://$(LISTEN_HOST):$(LISTEN_PORT)/"
	@ tcpserver -v "$(LISTEN_HOST)" "$(LISTEN_PORT)" tinysite httpd

sync : force
	rsync -avzp --exclude ".*" "$(OUT)/" "$(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)/"

clean :
	@ rm -rvf $(PAGES) $(DEPS) $(BUILD_ROOT)


### Scan templates and content+data for file dependencies.
### Ensures correct incremental builds.

deps : $(DEPS)

$(BUILD_ROOT)/%.d : $(TEMPLATE_ROOT)/% $(CONTENT_ROOT)/%.md
	@ mkdir -p `dirname "$@"`
	@ $(HIGHLIGHT_SCAN) scan "$(@:${BUILD_ROOT}/%.d=/%)"
	@ tinysite scan "$(@:${BUILD_ROOT}/%.d=${STATIC_ROOT}/%)" | sed -nEe "p; s@^${STATIC_ROOT}(.+?) :@\n${BUILD_ROOT}\1.d :@p;" > "$@"

ifeq (, $(findstring $(MAKECMDGOALS), clean ))
  -include $(DEPS)
endif



.PHONY : force

### Delete $@ if a rule fails. GNU make-specific.
.DELETE_ON_ERROR :

