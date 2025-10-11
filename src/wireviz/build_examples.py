#!/usr/bin/env python3

import os
import sys
from pathlib import Path

import typer

from wireviz import APP_NAME, __version__, wireviz
from wireviz.helper import open_file_append, open_file_read, open_file_write

script_path = Path(__file__).absolute()

sys.path.insert(0, str(script_path.parent.parent))  # to find wireviz module


dir = script_path.parent.parent.parent
readme = "readme.md"
groups = {
    "examples": {
        "path": dir / "examples",
        "prefix": "ex",
        readme: [],  # Include no files
        "title": "Example Gallery",
    },
    "tutorial": {
        "path": dir / "tutorial",
        "prefix": "tutorial",
        readme: ["md", "yml"],  # Include .md and .yml files
        "title": f"{APP_NAME} Tutorial",
    },
    "demos": {
        "path": dir / "examples",
        "prefix": "demo",
    },
}

input_extensions = [".yml"]
extensions_not_containing_graphviz_output = [".gv", ".bom.tsv"]
extensions_containing_graphviz_output = [".png", ".svg", ".html"]
generated_extensions = (
    extensions_not_containing_graphviz_output + extensions_containing_graphviz_output
)


def collect_filenames(description: str, groupkey: str, ext_list: list[str]) -> list[Path]:
    """Collect filenames matching extensions for a specific group.

    Args:
        description: Description of the action (e.g., "Building", "Cleaning").
        groupkey: Key identifying the file group to process.
        ext_list: List of file extensions to match.

    Returns:
        Sorted list of matching file paths.

    """
    path = groups[groupkey]["path"]
    patterns = [f"{groups[groupkey]['prefix']}*{ext}" for ext in ext_list]
    if ext_list != input_extensions and readme in groups[groupkey]:
        patterns.append(readme)
    return sorted([filename for pattern in patterns for filename in path.glob(pattern)])


def build_generated(groupkeys: list[str]) -> None:
    """Build generated files (diagrams, BOMs, etc.) from YAML input files.

    Args:
        groupkeys: List of group keys to process.

    """
    for key in groupkeys:
        # preparation
        path = groups[key]["path"]
        build_readme = readme in groups[key]
        if build_readme:
            include_readme = "md" in groups[key][readme]
            include_source = "yml" in groups[key][readme]
            with open_file_write(path / readme) as out:
                out.write(f"# {groups[key]['title']}\n\n")
        # collect and iterate input YAML files
        for yaml_file in collect_filenames("Building", key, input_extensions):
            wireviz.parse(yaml_file, output_formats=("gv", "html", "png", "svg", "tsv"))

            if build_readme:
                i = "".join(filter(str.isdigit, yaml_file.stem))

                with open_file_append(path / readme) as out:
                    if include_readme:
                        with open_file_read(yaml_file.with_suffix(".md")) as info:
                            for line in info:
                                out.write(line.replace("## ", f"## {i} - "))
                            out.write("\n\n")
                    else:
                        out.write(f"## Example {i}\n")

                    if include_source:
                        with open_file_read(yaml_file) as src:
                            out.write("```yaml\n")
                            for line in src:
                                out.write(line)
                            out.write("```\n")
                        out.write("\n")

                    out.write(f"![]({yaml_file.stem}.png)\n\n")
                    out.write(
                        f"[Source]({yaml_file.name}) - [Bill of Materials]({yaml_file.stem}.bom.tsv)\n\n\n",
                    )


def clean_generated(groupkeys: list[str]) -> None:
    """Remove all generated files for specified groups.

    Args:
        groupkeys: List of group keys to clean.

    """
    for key in groupkeys:
        # collect and remove files
        for filename in collect_filenames("Cleaning", key, generated_extensions):
            if filename.is_file():
                Path(filename).unlink()


def compare_generated(groupkeys: list[str], branch: str = "", include_graphviz_output: bool = False) -> None:
    """Compare generated files with those in a git branch.

    Args:
        groupkeys: List of group keys to compare.
        branch: Git branch or commit to compare against. Empty string for staged changes.
        include_graphviz_output: Whether to include Graphviz output files (PNG, SVG, HTML) in comparison.

    """
    if branch:
        branch = f" {branch.strip()}"
    compare_extensions = (
        generated_extensions
        if include_graphviz_output
        else extensions_not_containing_graphviz_output
    )
    for key in groupkeys:
        # collect and compare files
        for filename in collect_filenames("Comparing", key, compare_extensions):
            cmd = f'git --no-pager diff{branch} -- "{filename}"'
            os.system(cmd)


def restore_generated(groupkeys: list[str], branch: str = "") -> None:
    """Restore generated files from a git branch.

    Args:
        groupkeys: List of group keys to restore.
        branch: Git branch or commit to restore from. Empty string for HEAD.

    """
    if branch:
        branch = f" {branch.strip()}"
    for key in groupkeys:
        # collect input YAML files
        filename_list = collect_filenames("Restoring", key, input_extensions)
        # collect files to restore
        filename_list = [
            fn.with_suffix(ext) for fn in filename_list for ext in generated_extensions
        ]
        if readme in groups[key]:
            filename_list.append(groups[key]["path"] / readme)
        # restore files
        for filename in filename_list:
            cmd = f'git checkout{branch} -- "{filename}"'
            os.system(cmd)


def version_callback(value: bool) -> None:
    """Typer callback to display version and exit.

    Args:
        value: If True, displays version and exits.

    """
    if value:
        typer.echo(f"{APP_NAME} Example Manager - {APP_NAME} {__version__}")
        raise typer.Exit


def main(
    action: str = typer.Argument(
        "build",
        help="what to do with the generated files (default: build)",
    ),
    compare_graphviz_output: bool = typer.Option(
        False,
        "-c",
        "--compare-graphviz-output",
        help="the Graphviz output is also compared (default: False)",
    ),
    branch: str = typer.Option(
        "",
        "-b",
        "--branch",
        help="branch or commit to compare with or restore from",
    ),
    group_list: list[str] = typer.Option(
        list(groups.keys()),
        "-g",
        "--groups",
        help="the groups of generated files (default: all). Use multiple times: --groups examples --groups tutorial",
    ),
    version: bool = typer.Option(
        False,
        "-V",
        "--version",
        callback=version_callback,
        is_eager=True,
        help="show program's version number and exit",
    ),
) -> None:
    """WireViz Example Manager"""
    # Validate action choice
    valid_actions = ["build", "clean", "compare", "diff", "restore"]
    if action not in valid_actions:
        typer.echo(f"Error: Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}")
        raise typer.Exit(code=1)

    # Validate groups
    valid_groups = list(groups.keys())
    for group in group_list:
        if group not in valid_groups:
            typer.echo(f"Error: Invalid group '{group}'. Must be one of: {', '.join(valid_groups)}")
            raise typer.Exit(code=1)

    if action == "build":
        build_generated(group_list)
    elif action == "clean":
        clean_generated(group_list)
    elif action in {"compare", "diff"}:
        compare_generated(group_list, branch, compare_graphviz_output)
    elif action == "restore":
        restore_generated(group_list, branch)


if __name__ == "__main__":
    typer.run(main)
