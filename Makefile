# $Id$
prefix = /usr/local
py_files = autokey.py hotstring.py keyreader.py
all:
	gcc -o hotstring_logger keylogger.c

clean:
	rm -fr *.o hotstring_logger *.pyc

install:
	cp hotstring_logger *.py $(prefix)/bin
	cp autokey.desktop $(prefix)/share/applications
	cp autokey.py.1 $(prefix)/share/man/man1
	echo "You should copy the example abbr.ini to ~/.abbr.ini"
	echo "PLEASE READ THE INSTALL AND README FILES!"

uninstall:
	rm $(prefix)/bin/hotstring_logger $(prefix)/bin/autokey.py $(prefix)/bin/hotstring.py $(prefix)/bin/keyreader.py
	rm $(prefix)/share/applications/autokey.desktop
	rm $(prefix)/share/man/man1/autokey.py.1
