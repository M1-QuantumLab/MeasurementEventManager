# Configuration file for the Sphinx documentation builder.

import os
import sys

## Add path to package root
parent = os.path.dirname(os.path.dirname(__file__))
sys.path.append(parent)

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
    # 'sphinx.ext.autodoc',
    # 'sphinx.ext.autosummary',
    'autoapi.extension',
    'sphinx.ext.intersphinx',
    ## For Google or NumPy-style docstrings
    'sphinx.ext.napoleon',
    ## Dark mode for RTD theme
    'sphinx_rtd_dark_mode',
]

# autodoc_default_options = {
#     "show-inheritance": True,
#     "class-doc-from": "both",
# }
# autodoc_member_order = "groupwise"
# autodoc_mock_imports = ["pyHegel"]
autodoc_typehints = "description"
# autosummary_generate = True
autoapi_add_toctree_entry = False
autoapi_dirs = ['../measurement_event_manager']
autoapi_keep_files = True
autoapi_member_order = "groupwise"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]
autoapi_own_page_level = "class"
autoapi_python_class_content = "both"
autoapi_python_use_implicit_namespaces = True
autoapi_template_dir = "_templates"
autoapi_type = "python"

napoleon_google_docstring = True
napoleon_numpy_docstring = False


intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'
# html_theme = "furo"
# html_theme = "sphinx_book_theme"
# html_theme = "pydata_sphinx_theme"

html_theme_options = {
    ## RTD theme options
    "titles_only": True,
    ## Other theme options
    # "repository_url": "https://github.com/M1-QuantumLab/MeasurementEventManager",
    # "use_repository_button": True,
}

# -- Options for EPUB output
epub_show_urls = 'footnote'
