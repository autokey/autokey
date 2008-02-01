prefix = /usr/local
py_files = autokey.py hotstring.py keyreader.py
all:
	gcc -o hotstring_logger keylogger.c

clean:
	rm -fr *.o

install:
	cp hotstring_logger *.py $(prefix)/bin
	cp autokey.desktop $(prefix)/share/applications
	echo "You should copy the example abbr.ini to ~/.abbr.ini"

uninstall:
	rm $(prefix)/bin/hotstring_logger $(prefix)/bin/autokey.py $(prefix)/bin/hotstring.py $(prefix)/bin/keyreader.py
	rm $(prefix)/share/applications/autokey.desktop
