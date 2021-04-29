# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
#TODO this needs to be dealt with for github actions
sys.path.insert(0, os.path.abspath('../../lib'))


# -- Project information -----------------------------------------------------

project = 'AutoKey'
copyright = '2021, Various'
author = 'Various'

# The full version, including alpha/beta/rc tags
release = version = 'latest'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'recommonmark',
    'sphinx_rtd_theme',
    'sphinx_epytext',
]


# source_suffix = [
    # '.rst': 'restructuredtext',
    # '.md': 'markdown',

# ]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
    'README.md',
    'scripts',
    'old_wiki', #moved temporarily
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_logo = '../../config/autokey.png'
html_theme_options = {
    'logo_only': True,
    'display_version': True,
}
html_favicon = 'favicon.ico'

#TODO make this point to wherever the source files are goint to be hosted
# this enables the "edit on github behavior for the top right corners of webpages
html_context = {
    'display_github': True,
    'github_user': 'autokey',
    'github_repo': 'autokey',
    'github_version': 'docs/',
}

html_sidebars = {
    '**': [
        'versioning.html',
    ],
}

#added based on PR #487, required modules
autodoc_mock_imports = [
    "PyQt5",
    "gi",

]

# this code is to workaround the module docstring being posted at the top of every
# api page.
def skip_modules_docstring(app, what, name, obj, options, lines):
    print(what, name)
    if what == 'module':
        print(what, name, lines)
        del lines[:]

def setup(app):
    app.connect('autodoc-process-docstring', skip_modules_docstring)
