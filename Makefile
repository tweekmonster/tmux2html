SHELL := /bin/bash
PATH := node_modules/.bin:$(PATH)
TPL_PATH = tmux2html/templates
JS = $(wildcard assets/js/*.js)
HTML = $(JS:assets/js/%.js=$(TPL_PATH)/%.html)
STATIC = $(TPL_PATH)/static.html
CSS = .styles.css

.PHONY: help all clean js bump upload

help:		## This help message
	@echo -e "$$(grep -hE '^\S+:.*##' $(MAKEFILE_LIST) \
		| sed -e 's/:.*##\s*/:/' -e 's/^\(.\+\):\(.*\)/\\x1b[36m\1\\x1b[m:\2/' \
		| column -c2 -t -s :)"

all:		## Build everything
all: $(CSS) $(HTML) $(STATIC)
	@:

watch:	## Grandpa's change monitoring
	@while [ 1 ]; do \
		$(MAKE) --no-print-directory all; \
		sleep 0.5; \
	done; \
	true

clean:	## Cleanup
	rm -f $(HTML) $(CSS) $(STATIC)

bump:
	$(eval V := $(shell echo -n "$$(grep 'version=' setup.py | sed -ne "s/.*='\(.\+\)'\,/\1/p")"))
	$(eval NV := $(shell echo -n "$(V)" | awk -F'.' '{print $$1"."$$2"."$$3+1}'))
	sed -i -e 's/$(V)/$(NV)/g' setup.py
	git add setup.py
	git commit -m "Bump"
	git tag -a -m 'Auto bumped to $(NV)' $(NV)

upload:
	cat README.md | sed 's/@/\\@/' | pandoc -f markdown -t rst > README.rst
	python setup.py sdist upload -r pypi
	rm README.rst

$(CSS): assets/base.css
	cat $< | postcss --use autoprefixer --autoprefixer.browsers "last 4 versions" --use cssnano > $@

$(HTML): $(CSS) assets/tmux.html
$(HTML):$(TPL_PATH)/%.html:assets/js/%.js
	mkdir -p $(@D)
	cat assets/tmux.html > $@
	browserify -p bundle-collapser/plugin $< | uglifyjs -m -c warnings=false -o .script.js
	sed -i -e '/%CSS%/{ ' -e 'r .styles.css' -e 'd}' $@
	sed -i -e '/%JS%/{ ' -e 'r .script.js' -e 'd}' $@
	rm .script.js

$(STATIC): $(CSS)
$(STATIC): assets/tmux.html
	mkdir -p $(@D)
	cat $< > $@
	sed -i -e '/%CSS%/{ ' -e 'r .styles.css' -e 'd}' $@
	sed -i -e '/$$data/d' $@
	sed -i -e '/<script>/,/<\/script>/d' $@
