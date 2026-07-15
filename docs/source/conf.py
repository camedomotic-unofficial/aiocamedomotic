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
copyright = "2026, CAME Domotic Unofficial team"
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

# Serve the LLM documentation files (generated in the repo root by
# scripts/build_llms_docs.py) at the docs site root, so that the
# conventional https://aiocamedomotic.readthedocs.io/latest/llms.txt
# lookup works.
html_extra_path = ["../../llms.txt", "../../llms-full.txt"]


# -- Options for Markdown output -----------------------------------------------
markdown_anchor_sections = True
markdown_anchor_signatures = True


def setup(app):
    """Register handlers for node types sphinx-markdown-builder can't render.

    Without these, the builder logs "unknown node type" and silently drops
    the node and all its content: the keyword-only ``*`` marker in autodoc
    signatures (wrapped in an abbreviation node since Sphinx 8.2) and the
    body of ``danger``/``tip`` admonitions would disappear from llms*.txt.
    The handlers are no-ops so the builder descends into the children and
    renders their text; admonitions additionally get a bold label, matching
    how the LLM docs render the natively supported admonition types.
    """
    from docutils import nodes

    def _noop(self, node):
        pass

    def _labelled(label):
        def visit(self, node):
            node.insert(0, nodes.paragraph("", "", nodes.strong(text=f"{label}:")))

        return visit

    app.add_node(nodes.abbreviation, override=True, markdown=(_noop, _noop))
    app.add_node(nodes.danger, override=True, markdown=(_labelled("DANGER"), _noop))
    app.add_node(nodes.tip, override=True, markdown=(_labelled("TIP"), _noop))
