all: wayland weston

PYTHON = python

XMLS = $(wildcard ../wayland/protocol/*.xml) $(wildcard ../weston/protocol/*.xml)
TEMPLATES = $(wildcard doc/templates/*)

GENERATED_FILES = \
	doc/wayland/index.html \
	doc/weston/index.html

wayland: doc/wayland/index.html
weston: doc/weston/index.html

xml/wayland/wayland.xml:
	mkdir -p xml/wayland
	wget -nc "http://cgit.freedesktop.org/wayland/wayland/plain/protocol/wayland.xml" -O $@

# I can't believe this is easier than doing something with the git repository.
xml/weston/index.html:
	mkdir -p xml/weston
	wget -nc -r -l 1 -nH --cut-dirs=4 "http://cgit.freedesktop.org/wayland/weston/plain/protocol/" --directory-prefix=xml/weston

$(GENERATED_FILES): xml/wayland/wayland.xml xml/weston/index.html tools/doc-generator.py tools/protocolparser.py $(TEMPLATES)
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
