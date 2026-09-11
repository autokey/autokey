FN = autokey-gnome-extension@autokey.shell-extension.zip

VERSION = $(shell gnome-shell --version | awk '{print int($$3)}')
ifeq ($(filter $(VERSION), 40 41 42 43 44),)
	BUILD_VERSION=46
else
	BUILD_VERSION=44
endif

all: publish

publish:
	rm -f $(FN)
	@echo "Building $(FN) for Gnome version $(VERSION)"
	zip --junk-paths $(FN) $(BUILD_VERSION)/extension.js $(BUILD_VERSION)/metadata.json

version:
	@echo 'This system is running Gnome version $(version)'

clean:
	rm -f $(FN)
