all: wayland weston

PYTHON = python

XMLS = $(wildcard ../wayland/protocol/*.xml) $(wildcard ../weston/protocol/*.xml)
TEMPLATES = $(wildcard doc/templates/*)

GENERATED_FILES = \
	doc/wayland/index.html \
	doc/weston/index.html

wayland: doc/wayland/index.html
weston: doc/weston/index.html

$(GENERATED_FILES): $(XMLS) tools/doc-generator.py tools/protocolparser.py $(TEMPLATES)
	@dir=`dirname $@`; \
	project=`basename $$dir`; \
	rm -rf $$dir; \
	install -d $$dir; \
	$(PYTHON) tools/doc-generator.py ../$$project/protocol $$dir $$project

upload: all
	scp -r doc/weston doc/wayland dhansak:public_html/

all: $(GENERATED_FILES)
	@echo "Your protocol HTML starts at:"
	@echo
	@for i in $(GENERATED_FILES); do \
		echo file://$(CURDIR)/$$i; \
	done
	@echo

clean:
	rm -rf doc/wayland
	rm -rf doc/weston
	rm -rf tmp

.PHONY: \
    all \
    clean \
    wayland \
    weston \
    upload
