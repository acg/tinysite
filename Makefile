all : compiled-python


### Compile all python modules ahead of time.

PYTHON_SOURCE_FILES   := $(shell find lib -type f -a -name "*.py" -a -not -name ".*")
PYTHON_COMPILED_FILES := $(PYTHON_SOURCE_FILES:%.py=%.pyo)

compiled-python : $(PYTHON_COMPILED_FILES)

%.pyo : %.py
	python -O -m py_compile $<


clean :
	rm -f $(PYTHON_COMPILED_FILES)


.PHONY : clean force

### Delete $@ if a rule fails. GNU make-specific.
.DELETE_ON_ERROR :

