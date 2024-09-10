# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'MeasurementEventManager'
copyright = '2023-2024, Sam Wolski'
author = 'Sam Wolski'

release = '0.1'
version = '0.1.0'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    ## For Google or NumPy-style docstrings
    'sphinx.ext.napoleon',
]

autodoc_mock_imports = ["pyHegel"]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'
