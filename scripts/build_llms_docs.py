#!/usr/bin/env python3
"""Build llms.txt and llms-full.txt from Sphinx-generated Markdown files.

This script uses sphinx-markdown-builder to render the project's Sphinx
documentation (including autodoc-resolved API reference) into Markdown,
then assembles two LLM-optimized documentation files:

  - llms.txt      : Summary (overview + getting started)
  - llms-full.txt : Full reference (overview + getting started + usage
                   examples + complete API reference)

Prerequisites:
  pip install -e .
  pip install -r docs/source/requirements.txt

Usage:
  # Full build (runs sphinx-build, then assembles):
  python scripts/build_llms_docs.py

  # Skip sphinx-build (use existing docs/build/markdown/ output):
  python scripts/build_llms_docs.py --skip-sphinx-build

  # Write output to a custom directory:
  python scripts/build_llms_docs.py --output-dir /tmp/out

  # Show help:
  python scripts/build_llms_docs.py --help
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_SOURCE = PROJECT_ROOT / "docs" / "source"
MD_BUILD_DIR = PROJECT_ROOT / "docs" / "build" / "markdown"

SECTION_FILES = {
    "index": "index.md",
    "getting_started": "getting_started.md",
    "usage_examples": "usage_examples.md",
    "api_reference": "api_reference.md",
}


def run_sphinx_build():
    """Run sphinx-build with the markdown builder."""
    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        "-b",
        "markdown",
        str(DOCS_SOURCE),
        str(MD_BUILD_DIR),
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        print(f"sphinx-build failed with return code {result.returncode}", file=sys.stderr)
        sys.exit(1)


def read_section(name: str) -> str:
    """Read a generated markdown file by section name."""
    path = MD_BUILD_DIR / SECTION_FILES[name]
    if not path.exists():
        print(f"Warning: {path} not found, skipping section '{name}'", file=sys.stderr)
        return ""
    return path.read_text(encoding="utf-8")


def clean_markdown(content: str) -> str:
    """Clean up sphinx-markdown-builder output artifacts."""
    # Remove empty anchor references like []() or [](...)
    content = re.sub(r"\[\]\([^)]*\)", "", content)
    # Remove :doc: and :ref: artifacts that were not resolved
    content = re.sub(r":doc:`([^`]*)`", r"\1", content)
    content = re.sub(r":ref:`([^`]*)`", r"\1", content)
    # Remove sphinx-specific HTML comments
    content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    # Remove anchor tags like <a id="..."></a>
    content = re.sub(r'<a id="[^"]*"></a>\s*', "", content)
    # Remove the autodoc "NOTE" about dynamic page creation
    content = re.sub(
        r"^#{1,6}\s+NOTE\s*\nThis page is dynamically created using the\s*\n"
        r"\[sphinx\.ext\.autodoc\]\([^)]*\)\s*\nextension\.\s*\n*",
        "",
        content,
        flags=re.MULTILINE,
    )
    # Normalize multiple consecutive blank lines to two
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def adjust_heading_levels(content: str, increase_by: int = 1) -> str:
    """Increase heading levels (e.g. # -> ##) to nest under a parent heading.

    Skips content inside fenced code blocks.
    """
    lines = content.split("\n")
    result = []
    in_code_block = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
        if not in_code_block:
            line = re.sub(
                r"^(#{1,5})([ \t])",
                lambda m: "#" * (len(m.group(1)) + increase_by) + m.group(2),
                line,
            )
        result.append(line)
    return "\n".join(result)


def fix_internal_links(content: str) -> str:
    """Convert inter-file links to in-file anchors."""
    # Replace links like [text](getting_started.md#section) -> [text](#section)
    # and [text](getting_started.md) -> [text](#getting-started)
    file_to_anchor = {
        "getting_started": "#getting-started",
        "usage_examples": "#usage-examples",
        "api_reference": "#api-reference",
        "index": "#aiocamedomotic",
        "genindex": "",
    }
    for name, anchor in file_to_anchor.items():
        # Links with section anchors: file.md#section -> #section
        content = re.sub(
            rf"\]\({re.escape(name)}\.md#([^)]*)\)", r"](#\1)", content
        )
        # Links without anchors: file.md -> #anchor
        content = content.replace(f"]({name}.md)", f"]({anchor})")
    # Remove links to genindex that are now broken
    content = re.sub(r"\*\s*\[Index\]\(\)\s*\n?", "", content)
    return content


def extract_overview(index_content: str) -> str:
    """Extract the overview content from index.md, removing toctree/nav/contents."""
    # Cut off everything from the "Contents" section onward (toctree + nav links)
    content = re.split(r'<a id="contents"></a>', index_content, maxsplit=1)[0]
    # Remove anchor tags like <a id="welcome"></a>
    content = re.sub(r'<a id="[^"]*"></a>\s*', "", content)
    return content


def build_header() -> str:
    """Build the document header."""
    return (
        "# aiocamedomotic\n\n"
        "> Async Python library for interacting with CAME Domotic home automation "
        "systems. Provides automatic session management and device control.\n"
    )


def assemble_llms_md(overview: str, getting_started: str) -> str:
    """Assemble the summary llms.txt file."""
    parts = [
        build_header(),
        "",
        overview,
        "",
        getting_started,
        "",
        "---",
        "",
        "For complete usage examples and full API reference, see "
        "[llms-full.txt](llms-full.txt).",
        "",
    ]
    content = "\n".join(parts)
    content = fix_internal_links(content)
    content = clean_markdown(content)
    return content + "\n"


def assemble_llms_full_md(
    overview: str,
    getting_started: str,
    usage_examples: str,
    api_reference: str,
) -> str:
    """Assemble the full llms-full.txt file."""
    parts = [
        build_header(),
        "",
        overview,
        "",
        getting_started,
        "",
        usage_examples,
        "",
        api_reference,
        "",
    ]
    content = "\n".join(parts)
    content = fix_internal_links(content)
    content = clean_markdown(content)
    return content + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Build llms.txt and llms-full.txt from Sphinx markdown output."
    )
    parser.add_argument(
        "--skip-sphinx-build",
        action="store_true",
        help="Skip running sphinx-build (use existing docs/build/markdown/ output).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT,
        help="Output directory for llms.txt and llms-full.txt (default: project root).",
    )
    args = parser.parse_args()

    if not args.skip_sphinx_build:
        run_sphinx_build()

    if not MD_BUILD_DIR.exists():
        print(
            f"Error: {MD_BUILD_DIR} does not exist. "
            "Run sphinx-build first or remove --skip-sphinx-build.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Read sections
    index_raw = read_section("index")
    getting_started_raw = read_section("getting_started")
    usage_examples_raw = read_section("usage_examples")
    api_reference_raw = read_section("api_reference")

    # Process sections
    overview = extract_overview(index_raw)
    overview = adjust_heading_levels(overview, increase_by=1)
    overview = clean_markdown(overview)

    getting_started = adjust_heading_levels(getting_started_raw, increase_by=1)
    getting_started = clean_markdown(getting_started)

    usage_examples = adjust_heading_levels(usage_examples_raw, increase_by=1)
    usage_examples = clean_markdown(usage_examples)

    api_reference = adjust_heading_levels(api_reference_raw, increase_by=1)
    api_reference = clean_markdown(api_reference)

    # Assemble output files
    args.output_dir.mkdir(parents=True, exist_ok=True)

    llms_path = args.output_dir / "llms.txt"
    llms_content = assemble_llms_md(overview, getting_started)
    llms_path.write_text(llms_content, encoding="utf-8")
    print(f"Written: {llms_path} ({len(llms_content)} bytes)")

    llms_full_path = args.output_dir / "llms-full.txt"
    llms_full_content = assemble_llms_full_md(
        overview, getting_started, usage_examples, api_reference
    )
    llms_full_path.write_text(llms_full_content, encoding="utf-8")
    print(f"Written: {llms_full_path} ({len(llms_full_content)} bytes)")


if __name__ == "__main__":
    main()
