TINYSITE_ROOT ?= $(CURDIR)

### Custom shell for all rules in this Makefile.
SHELL = sh -c '. "$$0"/etc/main.env && exec bash -o pipefail "$$@"' "$(TINYSITE_ROOT)"

IN           ?= content
OUT          ?= static
TEMPLATE_DIR ?= templates

CONTENT_FILES = $(shell find ${IN} -type f -a -name \*.md)
PAGES         = $(CONTENT_FILES:${IN}/%.md=${OUT}/%.html)


all : pages

pages : $(PAGES)

$(OUT)/%.html : $(TEMPLATE_DIR)/%.html $(IN)/%.md
	@ mkdir -p `dirname "$@"`
	tinysite "$(TEMPLATE_DIR)" "$(IN)" "$(OUT)" "$(@:${OUT}%=%)" > "$@"

sync : force
	rsync -avzp --exclude ".*" "$(OUT)/" "$(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)/"

clean :
	rm -f $(PAGES)


# TODO include *.d scanner-generated dependency files here.


.PHONY : force

### Delete $@ if a rule fails. GNU make-specific.
.DELETE_ON_ERROR :

