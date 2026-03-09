# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

_conf_dir = os.path.dirname(os.path.abspath(__file__))
module_path = os.path.abspath(os.path.join(_conf_dir, "..", ".."))
sys.path.insert(0, module_path)

# Read version from pyproject.toml
_pyproject_path = os.path.join(module_path, "pyproject.toml")
with open(_pyproject_path, "rb") as f:
    _pyproject = tomllib.load(f)
release = _pyproject["tool"]["poetry"]["version"]

project = "aiocamedomotic"
copyright = "2024, CAME Domotic Unofficial team"
author = "fredericks1982"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_rtd_theme",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx_markdown_builder",
]

templates_path = ["_templates"]
exclude_patterns = exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Options for Markdown output -----------------------------------------------
markdown_anchor_sections = True
markdown_anchor_signatures = True
