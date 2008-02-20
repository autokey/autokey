# $Id$
prefix = /usr/local
mod_prefix = $(prefix)
py_modules = 
all:
	gcc -o hotstring_logger keylogger.c

clean:
	rm -fr *.o hotstring_logger *.pyc

install:
	sed "s#/usr/local/share/autokey#$(mod_prefix)/share/autokey#" autokey.py > $(prefix)/bin/autokey.py
	chmod a+x $(prefix)/bin/autokey.py
	cp hotstring_logger $(prefix)/bin
	cp autokey.desktop $(prefix)/share/applications
	cp autokey.py.1 $(prefix)/share/man/man1
	# local modules will be byte compiled and copied to $(prefix)/share/autokey in the future
	echo "You should copy the example abbr.ini to ~/.abbr.ini"
	echo "PLEASE READ THE INSTALL AND README FILES!"

uninstall:
	rm $(prefix)/bin/hotstring_logger
	rm $(prefix)/bin/autokey.py
	rm -fr $(prefix)/share/autokey/
	rm $(prefix)/share/applications/autokey.desktop
	rm $(prefix)/share/man/man1/autokey.py.1
