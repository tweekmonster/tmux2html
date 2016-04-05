SHELL := /bin/bash
PATH := node_modules/.bin:$(PATH)
TPL_PATH = tmux2html/templates
JS = $(wildcard assets/js/*.js)
HTML = $(JS:assets/js/%.js=$(TPL_PATH)/%.html)
STATIC = $(TPL_PATH)/static.html
CSS = .styles.css

.PHONY: all clean js

all: $(CSS) $(HTML) $(STATIC)

clean:
	rm -f $(HTML) $(CSS) $(STATIC)

$(CSS): assets/base.css
	cat $< | postcss --use autoprefixer --autoprefixer.browsers "last 4 versions" --use cssnano > $@

$(HTML): $(CSS)
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
