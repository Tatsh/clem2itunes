#!/usr/bin/env python3
"""Fix pyproject.toml for older Poetry versions.

This script modifies pyproject.toml to add required fields to [tool.poetry]
section from [project] section for compatibility with older Poetry versions
used in snapcraft builds.
"""

from __future__ import annotations

from pathlib import Path
import sys

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found]


def main() -> int:
    """Add required Poetry fields from [project] section to [tool.poetry] section."""
    pyproject_path = Path('pyproject.toml')
    if not pyproject_path.exists():
        return 1

    # Read the current pyproject.toml
    content = pyproject_path.read_text(encoding='utf-8')

    # Parse TOML to extract values
    with pyproject_path.open('rb') as f:
        data = tomllib.load(f)

    # Extract required fields from [project]
    project = data.get('project', {})
    required = [
        project.get('name'),
        project.get('version'),
        project.get('description'),
        project.get('authors', []),
    ]
    if not all(required):
        return 1

    # Format authors for Poetry (list of strings in "Name <email>" format)
    authors = []
    for author in project.get('authors', []):
        author_name = author.get('name', '')
        author_email = author.get('email', '')
        if author_name and author_email:
            authors.append(f'{author_name} <{author_email}>')
        elif author_name:
            authors.append(author_name)

    # Find the [tool.poetry] section and add the fields
    lines = content.split('\n')
    new_lines = []
    poetry_section_found = False

    for i, line in enumerate(lines):
        new_lines.append(line)

        # Check if we found the [tool.poetry] section
        if line.strip() == '[tool.poetry]':
            poetry_section_found = True
            # Add the required fields right after [tool.poetry]
            # Look ahead to see what's already there
            j = i + 1
            has_authors = False
            has_description = False
            has_name = False
            has_version = False

            while j < len(lines):
                next_line = lines[j].strip()
                if next_line.startswith('['):
                    break
                if next_line.startswith('authors'):
                    has_authors = True
                if next_line.startswith('description'):
                    has_description = True
                if next_line.startswith('name'):
                    has_name = True
                if next_line.startswith('version'):
                    has_version = True
                j += 1

            # Add missing fields
            if not has_authors:
                authors_str = ', '.join(f'"{a}"' for a in authors)
                new_lines.append(f'authors = [{authors_str}]')
            if not has_description:
                new_lines.append(f'description = "{project.get("description")}"')
            if not has_name:
                new_lines.append(f'name = "{project.get("name")}"')
            if not has_version:
                new_lines.append(f'version = "{project.get("version")}"')

    if not poetry_section_found:
        return 1

    # Write the modified content back
    pyproject_path.write_text('\n'.join(new_lines), encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
