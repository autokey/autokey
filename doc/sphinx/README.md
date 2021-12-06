# Autokey Documentation

Built using [sphinx]().

Uses the [sphinx autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) extension to automatically generate API documentation.

Uses the [sphinx epytext]() extension to convert older style epydoc documentation format to sphinx readable.

I also have it set to use [recommonmark]() in case any one wants to use markdown really badly.

The old wiki pages, while written in markdown are easily converted using the bash script provided, `pdmdtorst.sh` (PanDocMarkDownTORST). Run this in the base of the wiki repo and it will generate a `.rst` file for every `.md` file found.




## Local testing
You'll need the following python packages (and dependencies). From my command history getting it up and running;
- `pip install -U Sphinx`
- `pip install recommonmark`
- `pip install sphinx-rtd-theme`
- `pip install sphinx-epytext`
- `sudo apt install python3-tk`
- `sphinx-build -a -E -b html . ./_build`

`-a` for write all files, `-E` for always read all files, `-b html` for output to be in html format.

You can also generate the documentation using the `tox` test system;
`tox -e docs`

If you find that some of the API pages are generating without any content, it is probably because some part of the process failed, for me it failed because the `tkinter` module was not installed. 

I was able to Resolve this by installing the package for it; `sudo apt install python3-tkinter`


## TODO
There is a plugin that supports versioned documentation, [sphinxcontrib-multiversion](https://github.com/Holzhaus/sphinx-multiversion) which seems to be decently well maintained.

