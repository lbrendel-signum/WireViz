import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import wireviz.wireviz as wv
from wireviz import APP_NAME, __version__
from wireviz.helper import file_read_text

# Global console for rich output
console = Console()

app = typer.Typer()

format_codes = {
    # "c": "csv",
    "g": "gv",
    "h": "html",
    "p": "png",
    # "P": "pdf",
    "s": "svg",
    "t": "tsv",
}


def wireviz(
    file: list[str],
    output_name: str | None = None,
    format: str | None = "hpst",
    prepend: list[str] | None = None,
    output_dir: Path | None = ".\\",
    version: bool | None = False,
    quiet: bool | None = False,
) -> None:
    """
    Parses the provided FILE and generates the specified outputs.
    """
    if not quiet:
        console.print(f"\n[bold cyan]{APP_NAME}[/bold cyan] [cyan]{__version__}[/cyan]")
    else:
        print()
        print(f"{APP_NAME} {__version__}")
    if version:
        return  # print version number only and exit

    # get list of files
    try:
        _ = iter(file)
    except TypeError:
        filepaths = [file]
    else:
        filepaths = list(file)

    # determine output formats
    output_formats = []
    for code in format:
        if code in format_codes:
            output_formats.append(format_codes[code])
        else:
            raise Exception(f"Unknown output format: {code}")
    output_formats = tuple(sorted(set(output_formats)))
    output_formats_str = (
        f"[{'|'.join(output_formats)}]" if len(output_formats) > 1 else output_formats[0]
    )

    # check prepend file
    if prepend and len(prepend) > 0:
        prepend_input = ""
        for prepend_file in prepend:
            prepend_file = Path(prepend_file)
            if not prepend_file.exists():
                raise Exception(f"File does not exist:\n{prepend_file}")
            if not quiet:
                console.print(f"[dim]Prepend file: {prepend_file}[/dim]")
            else:
                print("Prepend file:", prepend_file)

            prepend_input += file_read_text(prepend_file) + "\n"
    else:
        prepend_input = ""

    # run WireVIz on each input file
    for fi in filepaths:
        f = Path(fi)
        if not f.exists():
            raise Exception(f"File does not exist:\n{f}")

        # file_out = file.with_suffix("") if not output_file else output_file
        _output_dir = f.parent if not output_dir else output_dir
        _output_name = f.stem if not output_name else output_name

        if not quiet:
            console.print(f"\n[bold]Processing:[/bold] [green]{f}[/green]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                task1 = progress.add_task("[cyan]Parsing input file...", total=None)
                yaml_input = file_read_text(f)
                file_dir = f.parent

                yaml_input = prepend_input + yaml_input
                image_paths = {file_dir}
                if prepend:
                    for p in prepend:
                        if p:  # Only add non-empty prepend paths
                            image_paths.add(Path(p).parent)

                progress.update(task1, description="[cyan]Building harness connections...")

                wv.parse(
                    yaml_input,
                    output_formats=output_formats,
                    output_dir=_output_dir,
                    output_name=_output_name,
                    image_paths=list(image_paths),
                )

                progress.update(task1, description="[green]✓ Complete")

            # Show individual output files
            console.print("[dim]Generated files:[/dim]")
            for fmt in output_formats:
                if fmt == "tsv":
                    output_path = Path(_output_dir) / f"{_output_name}.bom.{fmt}"
                else:
                    output_path = Path(_output_dir) / f"{_output_name}.{fmt}"
                console.print(f"  [dim]→[/dim] {output_path}")
        else:
            print("Input file:  ", f)
            print("Output file: ", f"{Path(_output_dir / _output_name)}.{output_formats_str}")

            yaml_input = file_read_text(f)
            file_dir = f.parent

            yaml_input = prepend_input + yaml_input
            image_paths = {file_dir}
            if prepend:
                for p in prepend:
                    if p:  # Only add non-empty prepend paths
                        image_paths.add(Path(p).parent)

            wv.parse(
                yaml_input,
                output_formats=output_formats,
                output_dir=_output_dir,
                output_name=_output_name,
                image_paths=list(image_paths),
            )

    if quiet:
        print()


if __name__ == "__main__":
    typer.run(wireviz)
