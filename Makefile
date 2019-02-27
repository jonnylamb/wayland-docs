all: wayland weston

PYTHON = python

XMLS = $(wildcard ../wayland/protocol/*.xml) $(wildcard ../weston/protocol/*.xml)
TEMPLATES = $(wildcard doc/templates/*)

GENERATED_FILES = \
	doc/wayland/index.html \
	doc/weston/index.html

wayland: doc/wayland/index.html
weston: doc/weston/index.html

# symlinked because it's easier as that's what the tp-spec script expects
xml/wayland:
	mkdir -p xml
	ln -s $$(pwd)/../wayland/protocol xml/wayland

xml/weston:
	mkdir -p xml
	ln -s $$(pwd)/../weston/protocol xml/weston

$(GENERATED_FILES): $(XMLS) xml/wayland xml/weston tools/doc-generator.py tools/protocolparser.py $(TEMPLATES)
	@dir=`dirname $@`; \
	project=`basename $$dir`; \
	rm -rf $$dir; \
	install -d $$dir; \
	$(PYTHON) tools/doc-generator.py xml/$$project $$dir $$project

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
	rm -rf xml
	rm -rf doc/wayland
	rm -rf doc/weston
	rm -rf tmp

.PHONY: \
    all \
    clean \
    wayland \
    weston \
    upload
